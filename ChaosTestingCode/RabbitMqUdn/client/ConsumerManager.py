from BrokerManager import BrokerManager
from MessageMonitor import MessageMonitor
from MultiTopicConsumer import MultiTopicConsumer
from printer import console_out
import random
from random import shuffle
import time
import threading
from printer import console_out_exception

class ConsumerManager:
    def __init__(self, broker_manager, msg_monitor, actor, use_toxiproxy):
        self.consumers = list()
        self.consumer_threads = list()
        self.broker_manager = broker_manager
        self.msg_monitor = msg_monitor
        self.actor = actor
        self.stop_random = False
        self.use_toxiproxy = use_toxiproxy

    def add_consumers(self, consumer_count, test_number, queue_name, prefetch):
        for con_id in range (1, consumer_count+1):
            consumer = MultiTopicConsumer(con_id, test_number, self.broker_manager, self.msg_monitor, prefetch)
            consumer.connect()
            consumer.set_queue(queue_name)

            self.consumers.append(consumer)

    def start_consumers(self):
        for con_id in range(1, len(self.consumers)+1):
            con_thread = threading.Thread(target=self.consumers[con_id-1].consume)
            con_thread.start()
            self.consumer_threads.append(con_thread)
            console_out(f"consumer {con_id} started", self.actor)

    def add_consumer_and_start_consumer(self, test_number, queue_name, prefetch):
        con_id = len(self.consumers)+1
        consumer = MultiTopicConsumer(con_id, test_number, self.broker_manager, self.msg_monitor, prefetch)
        consumer.connect()
        consumer.set_queue(queue_name)
        self.consumers.append(consumer)
        con_thread = threading.Thread(target=self.consumers[con_id-1].consume)
        con_thread.start()
        self.consumer_threads.append(con_thread)
        console_out(f"consumer {con_id} started", self.actor)
        
    def stop_and_remove_oldest_consumer(self):
        if len(self.consumers) > 0:
            self.stop_and_remove_specfic_consumer_index(0)

    def stop_and_remove_specfic_consumer(self, target_consumer):
        if len(self.consumers) > 0:
            for index in range(0, len(self.consumers)):
                if f"P{self.consumers[index].get_consumer_id()}" == target_consumer:
                    self.stop_and_remove_specfic_consumer_index(index)
                    return
            
            console_out(f"No consumer matches id: P{target_consumer}", self.actor)
                    
    def stop_and_remove_specfic_consumer_index(self, index):
        self.consumers[index].stop_consuming()
        self.consumer_threads[index].join(10)
        self.consumers.remove(self.consumers[index])
        self.consumer_threads.remove(self.consumer_threads[index])
        console_out("Consumer removed", self.actor)

    def do_consumer_action(self, hard_close):
        con_indexes = [i for i in range(len(self.consumers))]
        shuffle(con_indexes)

        # for 3 consumers, do an action on 1
        # for 5 consumers, do an action of 2 etc etc
        actions_count = max(1, int(len(self.consumers)/2))
        for i in range(actions_count):
            self.do_single_consumer_action(con_indexes[i], hard_close)

    def do_single_consumer_action(self, con_index, hard_close):
        con = self.consumers[con_index]
        if con.terminate == True:
            console_out(f"STARTING CONSUMER {con_index+1} --------------------------------------", self.actor)

            if self.use_toxiproxy:
                self.broker_manager.enable_consumer_proxy(con.get_consumer_id())

            con.connect()
            self.consumer_threads[con_index] = threading.Thread(target=con.consume)
            self.consumer_threads[con_index].start()
        else:
            try:
                if self.use_toxiproxy:
                    console_out(f"SIMULATING CRASH OF CONSUMER {con_index+1} --------------------------------------", self.actor)
                    self.broker_manager.disable_consumer_proxy(con.get_consumer_id())
                    time.sleep(1)
                    con.perform_hard_close()
                else:
                    console_out(f"STOPPING CONSUMER {con_index+1} --------------------------------------", self.actor)
                    if hard_close:
                        con.perform_hard_close()
                    else:
                        con.stop_consuming()
                self.consumer_threads[con_index].join(15)
            except Exception as e:
                template = "An exception of type {0} occurred. Arguments:{1!r}"
                message = template.format(type(e).__name__, e.args)
                console_out(f"Failed to stop consumer correctly: {message}", self.actor)

    def stop_start_consumers(self, hard_close):
        con_indexes = [i for i in range(len(self.consumers))]
        shuffle(con_indexes)

        # for 3 consumers, do an action on 1
        # for 5 consumers, do an action of 2 etc etc
        actions_count = max(1, int(len(self.consumers)/2))
        for i in range(actions_count):
            self.stop_start_consumer(con_indexes[i], hard_close)

    def stop_start_consumer(self, con_index, hard_close):
        con = self.consumers[con_index]
        try:
            if self.use_toxiproxy:
                console_out(f"SIMULATING CRASH OF CONSUMER {con_index+1} --------------------------------------", self.actor)
                self.broker_manager.disable_consumer_proxy(con.get_consumer_id())
                time.sleep(1)
                con.perform_hard_close()
                time.sleep(1)
                self.broker_manager.enable_consumer_proxy(con.get_consumer_id())
            else:
                console_out(f"STOPPING CONSUMER {con_index+1} --------------------------------------", self.actor)
                if hard_close:
                    con.perform_hard_close()
                else:
                    con.stop_consuming()
            self.consumer_threads[con_index].join(15)
            
            con.connect()
            self.consumer_threads[con_index] = threading.Thread(target=con.consume)
            self.consumer_threads[con_index].start()
        except Exception as e:
            console_out_exception("Failed to stop/start consumer correctly", e, self.actor)

    def get_running_consumer_count(self):
        running_cons = 0
        for con in self.consumers:
            if con.terminate == False:
                running_cons += 1

        return running_cons

    def start_random_stop_starts(self, min_seconds_interval, max_seconds_interval, hard_close):
        while self.stop_random == False:
            wait_sec = random.randint(min_seconds_interval, max_seconds_interval)
            console_out(f"Will execute stop/start consumer action in {wait_sec} seconds", self.actor)
            self.wait_for(wait_sec)

            if self.stop_random == False:
                try:
                    self.stop_start_consumers(hard_close)
                except Exception as e:
                    console_out_exception("Failed stopping/starting consumers", e, self.actor)

    def resume_all_consumers(self):
        for con_index in range(0, len(self.consumers)):
            if self.consumers[con_index].terminate == True:
                console_out(f"Starting consumer {con_index+1}", self.actor)
                if self.use_toxiproxy:
                    self.broker_manager.enable_consumer_proxy(self.consumers[con_index].get_consumer_id())

                self.consumers[con_index].connect()
                self.consumer_threads[con_index] = threading.Thread(target=self.consumers[con_index].consume)
                self.consumer_threads[con_index].start()

    def stop_all_consumers(self):
        for con in self.consumers:
            con.stop_consuming()

        for con_thread in self.consumer_threads:
            con_thread.join(15)

    def start_random_consumer_actions(self, min_seconds_interval, max_seconds_interval, hard_close):
        while self.stop_random == False:
            wait_sec = random.randint(min_seconds_interval, max_seconds_interval)
            console_out(f"Will execute consumer action in {wait_sec} seconds", self.actor)
            self.wait_for(wait_sec)

            if self.stop_random == False:
                try:
                    self.do_consumer_action(hard_close)
                except Exception as e:
                    console_out_exception("Failed performing consumer action", e, "TEST RUNNER")

    def stop_random_consumer_actions(self):
        self.stop_random = True

    def wait_for(self, seconds):
        ctr = 0
        while self.stop_random == False and ctr < seconds:
            ctr += 1
            time.sleep(1)