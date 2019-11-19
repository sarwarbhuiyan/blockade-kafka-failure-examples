import time
import datetime
from collections import deque

from printer import console_out

class MessageMonitor:
    def __init__(self, test_name, test_number, print_mod, analyze, log_messages):
        self.msg_queue = deque()
        self.msg_history = list()
        self.msg_set = set()
        self.last_consumer_ids = dict()
        self.last_consumer_tags = dict()
        self.keys = dict()
        self.receive_ctr = 0
        self.print_mod = print_mod
        self.out_of_order = False
        self.concurrent_consumers = False
        self.stop = False
        self.last_msg_time = datetime.datetime.now()
        self.analyze = analyze
        self.log_messages = log_messages
        self.event_of_interest = False

        if log_messages:
            msg_log_file = f"./logs/{test_name}/{test_number}/messages.txt"
            self.f = open(msg_log_file, "w")

    def append(self, message_body, consumer_tag, consumer_id, actor, redelivered):
        self.msg_queue.append((message_body, consumer_tag, consumer_id, actor, redelivered))

    def stop_processing(self):
        self.stop = True

    def log_message(self, message):
        self.msg_history.append(message)
        
        if len(self.msg_history) >= 1000:
            if self.event_of_interest:
                for msg in self.msg_history:
                    self.f.write(msg + "\n")
                
                self.f.write("...\n")
                self.event_of_interest = False

            self.msg_history.clear()


    def process_messages(self):
        console_out("monitor started", "MONITOR")
        while self.stop == False:
            try:
                msg_tuple = self.msg_queue.popleft()
                self.consume(msg_tuple[0], msg_tuple[1], msg_tuple[2], msg_tuple[3], msg_tuple[4])
                
                if self.log_messages:
                    self.log_message(f"{msg_tuple[0]}|{msg_tuple[2]}|{msg_tuple[3]}|{msg_tuple[4]}")
            except IndexError:
                time.sleep(1)
            except Exception as e:
                template = "An exception of type {0} occurred. Arguments:{1!r}"
                message = template.format(type(e).__name__, e.args)
                console_out(message, "MONITOR")
                time.sleep(1)
                
        if self.log_messages:
            for msg in self.msg_history:
                self.f.write(msg + "\n")
            self.f.close()
        console_out("Monitor exited", "MONITOR")

    def get_time(self, time_str):
        try:
            return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

    def consume(self, message_body, consumer_tag, consumer_id, actor, redelivered):
        self.last_msg_time = datetime.datetime.now()
        self.receive_ctr += 1
        body_str = str(message_body, "utf-8")
        time_part = body_str[0:body_str.find("|")]
        send_time = self.get_time(time_part)
        seconds_lag = f"           [Lag: {(datetime.datetime.now()-send_time).total_seconds()}s Sent: {send_time.time()}]"
        body_str = body_str[body_str.find("|")+1:]
        
        is_sequence = "=" in body_str
                
        if is_sequence and self.analyze:
            parts = body_str.split('=')
            key = parts[0]
            curr_value = int(parts[1])
            
            if key in self.last_consumer_tags:
                if self.last_consumer_tags[key] != consumer_tag:
                    console_out(f"CONSUMER CHANGE FOR SEQUENCE {key.upper()}! Last id: {self.last_consumer_ids[key]} New id: {consumer_id} Last tag: {self.last_consumer_tags[key]} New tag: {consumer_tag}", actor)
                    self.last_consumer_ids[key] = consumer_id
                    self.last_consumer_tags[key] = consumer_tag
                    self.event_of_interest = True
            else:
                console_out(f"CONSUMER STARTING CONSUMING SEQUENCE {key.upper()}! Consumer Id: {consumer_id} Consumer tag: {consumer_tag}", actor)
                self.last_consumer_ids[key] = consumer_id
                self.last_consumer_tags[key] = consumer_tag
                self.event_of_interest = True
            
            if body_str in self.msg_set:
                duplicate = f"DUPLICATE"
                is_dup = True
                self.event_of_interest = True
            else:
                duplicate = ""
                is_dup = False

            if redelivered:
                redelivered_str = "REDELIVERED"
                self.event_of_interest = True
            else:
                redelivered_str = ""

            self.msg_set.add(body_str)

            if key in self.keys:
                last_value = self.keys[key]
                
                if last_value + 1 < curr_value:
                    jump = curr_value - last_value
                    last = f"Last-acked={last_value}"
                    console_out(f"{body_str} {last} JUMP FORWARD {jump} {duplicate} {redelivered_str} {seconds_lag}", actor)
                    self.event_of_interest = True
                elif last_value > curr_value:
                    self.event_of_interest = True
                    jump = last_value - curr_value
                    last = f"Last-acked={last_value}"
                    
                    if is_dup == False and redelivered == False:
                        console_out(f"{body_str} {last} OUT-OF-ORDER!! JUMP BACK {jump} {duplicate} {redelivered_str} {seconds_lag}", actor)
                        self.out_of_order = True
                    else:
                        console_out(f"{body_str} {last} JUMP BACK {jump} {duplicate} {redelivered_str} {seconds_lag}", actor)
                elif self.receive_ctr % self.print_mod == 0:
                    console_out(f"Sample msg: {body_str} {duplicate} {redelivered_str} {seconds_lag}", actor)
                elif is_dup or redelivered:
                    self.event_of_interest = True
                    console_out(f"{body_str} {duplicate} {redelivered_str} {seconds_lag}", actor)
            else:
                self.event_of_interest = True
                if curr_value == 1:
                    console_out(f"{body_str} {duplicate} {redelivered_str} {seconds_lag}", actor)
                else:
                    console_out(f"{body_str} JUMP FORWARD {curr_value} {duplicate} {redelivered_str} {seconds_lag}", actor)
                    # self.out_of_order = True
            
            self.keys[key] = curr_value
        else:
            self.msg_set.add(body_str)
            if self.receive_ctr % self.print_mod == 0:
                if len(body_str) > 20:
                    body_str = body_str[0:20]
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

    def get_last_msg_time(self):
        return self.last_msg_time
