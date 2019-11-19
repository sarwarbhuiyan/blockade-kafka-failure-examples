import time
from collections import deque

from printer import console_out

class MessageMonitor:
    def __init__(self, print_mod, analyze):
        self.msg_queue = deque()
        self.msg_set = set()
        self.keys = dict()
        self.consumer_ids = dict()
        self.receive_ctr = 0
        self.print_mod = print_mod
        self.out_of_order = False
        self.concurrent_consumers = False
        self.stop = False
        self.last_message_body = ""
        self.sequential_dup_ctr = 0
        self.last_sequential_dup_ctr = 0
        self.analyze = analyze

    def append(self, message_body, consumer_id, actor):
        self.msg_queue.append((message_body, consumer_id, actor))

    def stop_processing(self):
        self.stop = True

    def process_messages(self):
        console_out("monitor started", "MONITOR")
        while self.stop == False:
            try:
                msg_tuple = self.msg_queue.popleft()
                self.consume(msg_tuple[0], msg_tuple[1], msg_tuple[2])
            except IndexError:
                time.sleep(1)
            except Exception as e:
                template = "An exception of type {0} occurred. Arguments:{1!r}"
                message = template.format(type(e).__name__, e.args)
                console_out(message, "MONITOR")
                time.sleep(1)
                

        console_out("Monitor exited", "MONITOR")

    def consume(self, message_body, consumer_id, actor):
        self.receive_ctr += 1
        body_str = str(message_body, "utf-8")
        
        if self.analyze:
            parts = body_str.split('=')
            key = parts[0]
            curr_value = int(parts[1])

            if body_str in self.msg_set:
                duplicate = f"DUPLICATE"
                is_dup = True
            else:
                duplicate = ""
                is_dup = False

            self.msg_set.add(body_str)

            if key in self.consumer_ids:
                if self.consumer_ids[key] != consumer_id:
                    console_out(f"CONSUMER CHANGE FOR SEQUENCE {key.upper()}! Last id: {self.consumer_ids[key]} New id: {consumer_id} Msg: {message_body} {duplicate}", actor)
                    self.consumer_ids[key] = consumer_id
            else:
                console_out(f"CONSUMER {consumer_id} CONSUMING SEQUENCE {key.upper()}! Msg: {message_body} {duplicate}", actor)
                self.consumer_ids[key] = consumer_id

            if key in self.keys:
                last_value = self.keys[key]

                if is_dup:
                    if last_value + 1 == curr_value:
                        self.sequential_dup_ctr += 1
                    else:
                        self.sequential_dup_ctr = 0
                else:
                    self.sequential_dup_ctr = 0
                
                if last_value + 1 < curr_value:
                    jump = curr_value - last_value
                    last = f"Last-acked={last_value}"
                    console_out(f"{message_body} {last} JUMP FORWARD {jump} {duplicate}", actor)
                elif last_value > curr_value:
                    jump = last_value - curr_value
                    last = f"Last-acked={last_value}"
                    console_out(f"{message_body} {last} JUMP BACK {jump} {duplicate}", actor)
                    if is_dup == False:
                        self.out_of_order = True
                elif self.receive_ctr % self.print_mod == 0:
                    console_out(f"Sample msg: {message_body} {duplicate}", actor)
                elif is_dup:
                    if self.sequential_dup_ctr <= 10:
                        console_out(f"Msg: {message_body} {duplicate}", actor)
                    elif self.sequential_dup_ctr == 11:
                        console_out(f"Too many duplicates...", actor)
                elif self.last_sequential_dup_ctr > 10:
                    console_out(f"Run of duplicates ended with {self.last_sequential_dup_ctr} duplicates and msg:{self.last_message_body}", actor)
            else:
                if curr_value == 1:
                    console_out(f"Latest msg: {message_body} {duplicate}", actor)
                else:
                    console_out(f"{message_body} JUMP FORWARD {curr_value} {duplicate}", actor)
                    self.out_of_order = True
            
            self.keys[key] = curr_value
            self.last_message_body = message_body
            self.last_sequential_dup_ctr = self.sequential_dup_ctr
        
        else:
            self.msg_set.add(body_str)
            if self.receive_ctr % self.print_mod == 0:
                console_out(f"Receive counter: {self.receive_ctr} Sample msg: {body_str}", actor)

    def stop_consuming(self):
        self.stop = True

    def get_msg_set(self):
        return self.msg_set

    def get_receive_count(self):
        return self.receive_ctr

    def get_unique_count(self):
        return len(self.msg_set)

    def get_out_of_order(self):
        return self.out_of_order