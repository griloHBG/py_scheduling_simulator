#-------------------------------------------------------------------------------
# Name:        scheduling_simulator
# Purpose:
#
# Author:      Henrique Garcia
#
# Created:     22/04/2018
# Copyright:   (c) Henrique Garcia 2018
# Licence:     SeiLá
#-------------------------------------------------------------------------------

from enum import Enum, auto

class CyclicTaskStates(Enum):
    READY = auto()
    FINISHED = auto()
    FAILED = auto()


class CyclicTask:

    def __init__(self, name: str, start_time: int, period: int, deadline: int, burst_time: int):
        if name == "":
            raise ValueError("name can't be \"void\"!")
        self._name = name

        if start_time < 0:
            raise ValueError("start_time can't be negative!")
        self._start_time = start_time

        if period <= 0:
            raise ValueError("period can't be negative nor zero!")
        self._period = period

        if burst_time <= 0:
            raise ValueError("burst_time can't be negative nor zero!")
        self._burst_time = burst_time

        if deadline > start_time + period:
            raise ValueError("deadline can't occur after second release!")
        self._deadline = deadline

        self._executed_time = 0
        self._current_period_begin = self._start_time
        self._current_deadline = self._start_time + self._deadline
        self._everything_started = False
        self._state = CyclicTaskStates.FINISHED
        
        self._reset_state = (self._name, self._start_time, self._period, self._burst_time, self._deadline, self._executed_time, self._current_period_begin, self._current_deadline, self._everything_started, self._state)

    def update(self, time: int):
        if time >= self._start_time and not self._everything_started:
            self._state = CyclicTaskStates.READY
            self._everything_started = True

        if time >= self._start_time and self._everything_started:
            task_time = time - self._current_period_begin
            if task_time == self._deadline:
                if self._state is not CyclicTaskStates.FINISHED:
                    self._state = CyclicTaskStates.FAILED
                    raise RuntimeError("CyclicTask \"{}\" FAILED at time {}!".format(self._name, time))
            if (task_time % self._period) == 0:
                self._executed_time = 0
                self._current_period_begin = time
                self._current_deadline = time + self._deadline
                self._state = CyclicTaskStates.READY

    def execute(self, time: int):
        if self._current_deadline < time and self._state is not CyclicTaskStates.FINISHED:
            self._state = CyclicTaskStates.FAILED

        if self._state is CyclicTaskStates.FAILED:
            raise RuntimeError("CyclicTask \"{}\" FAILED at time {}!".format(self._name, time))

        if time < self._start_time:
            raise RuntimeError("CyclicTask \"{}\" FAILED at time {}! (time < start_time)".format(self._name, time))

        self._executed_time += 1
        if self._executed_time == self._burst_time:
            self._state = CyclicTaskStates.FINISHED

    def get_current_deadline(self) -> int:
        return self._current_deadline

    def get_name(self) -> str:
        return self._name

    def is_ready(self) -> bool:
        return self._state == CyclicTaskStates.READY

    def get_state(self) -> CyclicTaskStates:
        return self._state

    def get_start_time(self) -> int:
        return self._start_time

    def get_period(self) -> int:
        return self._period

    def get_burst_time(self) -> int:
        return self._burst_time

    def get_deadline(self) -> int:
        return self._deadline

    def reset_task(self):
        self._name, self._start_time, self._period, self._burst_time, self._deadline, self._executed_time, self._current_period_begin, self._current_deadline, self._everything_started, self._state = self._reset_state


class EarliestDeadlineFirstScheduler:

    def __init__(self, tasks: list):
        if len(tasks) > (126 - 33 + 1):
            raise Exception("Can't deal with more than 94 processes!")
        self._tasks = tasks
        self._tasks_dict = {}
        self._history_dict = {}
        for task in tasks:
            self._tasks_dict[task.get_name()] = chr(48 + tasks.index(task))
            self._history_dict[task.get_name()] = ["{: >10}".format(task.get_name())]
        self._time = 0
        self._tasks_to_execute = []
        self._do_internal_round_robin = False
        self._internal_round_robin_counter = 0

        self._timeline_channel = ["{0: >10}".format("timeline")]
        self._error_list = []

    def update(self):
        for t in self._tasks:
            try:
                t.update(self._time)
            except RuntimeError as e:
                self._error_list.append(str(e))
            # print("{} | status: {: <25} | next dd: {}".format(t.get_name(), t.get_state(), t.get_current_deadline()))
        self._tasks_to_execute = []
        for task in self._tasks:
            if task.get_state() is CyclicTaskStates.READY:
                self._tasks_to_execute.append(task)
                break

        if self._tasks_to_execute:  # if self._tasks_to_execute is equal to []
            for task in self._tasks:
                if (task.get_current_deadline() < self._tasks_to_execute[0].get_current_deadline()
                 and task.get_state() == CyclicTaskStates.READY):
                    self._do_internal_round_robin = False
                    self._tasks_to_execute = []
                    self._tasks_to_execute.append(task)
                elif (task.get_current_deadline() == self._tasks_to_execute[0].get_current_deadline()
                 and task.get_state() == CyclicTaskStates.READY):
                    self._tasks_to_execute.append(task)
                    self._do_internal_round_robin = True

        try:
            self.execute()
        except RuntimeError as e:
            self._error_list.append(str(e))

        # for task in self._tasks:
        #    print("{}:{}".format(self._history_dict[task.get_name()][0],"".join(self._history_dict[task.get_name()][1:])))

        self._timeline_channel.append("-" if ((self._time - 1) % 10) == 0 else str((self._time - 1) % 10))
        # print("{}:{}".format(self._timeline_channel[0],"".join(self._timeline_channel[1:])))

    def execute(self):

        for task in self._tasks:
            self._history_dict[task.get_name()].append("-")

        if self._tasks_to_execute:  # if self._tasks_to_execute is equal to []
            task_to_execute = None
            if self._do_internal_round_robin:
                task_to_execute = self._tasks_to_execute[self._internal_round_robin_counter]
                self._internal_round_robin_counter += 1

                if self._internal_round_robin_counter == len(self._tasks_to_execute):
                    self._internal_round_robin_counter = 0
            else:
                task_to_execute = self._tasks_to_execute[0]

            try:
                task_to_execute.execute(self._time)
            except RuntimeError as e:
                self._error_list.append(str(e))

            self._history_dict[task_to_execute.get_name()][-1] = self._tasks_dict[task_to_execute.get_name()]
        self._time += 1

    def play(self, how_much: int):
        print("Earliest Deadline First - EDF")
        for i in range(how_much):
            try:
                self.update()
            except RuntimeError as e:
                self._error_list.append(str(e))
            if self._error_list:
                break

    def print_timeline(self):
        print("Earliest Deadline First - EDF")
        if self._error_list:
            print("FAILED!")
            for msg in self._error_list:
                print("\t{}".format(msg))
        print("Timeline:")
        for task in self._tasks:
            print("{}:{}".format(self._history_dict[task.get_name()][0], "".join(self._history_dict[task.get_name()][1:])))
        print("{}:{}".format(self._timeline_channel[0], "".join(self._timeline_channel[1:])))
        print()


class RoundRobinScheduler:

    def __init__(self, quantum: int, tasks: list):
        self._tasks = tasks
        self._quantum = quantum
        self._tasks_dict = {}
        self._history_dict = {}
        for task in tasks:
            self._tasks_dict[task.get_name()] = chr(48 + tasks.index(task))
            self._history_dict[task.get_name()] = ["{: >10}".format(task.get_name())]
        self._time = 0
        self._queue = []
        self._remaining_quantum = self._quantum

        self._timeline_channel = ["{0: >10}".format("timeline")]
        self._old_tasks_state = []
        self._error_list = []

    def update(self):
        self._old_tasks_state = [t.is_ready() for t in self._tasks]
        for i in range(len(self._tasks)):
            try:
                self._tasks[i].update(self._time)
            except RuntimeError as e:
                self._error_list.append(str(e))
            if self._tasks[i].get_state() is CyclicTaskStates.READY and not self._old_tasks_state[i]:
                self._queue.append(self._tasks[i])
        try:
            self.execute()
        except RuntimeError as e:
            self._error_list.append(str(e))

        self._timeline_channel.append("-" if ((self._time - 1) % 10) == 0 else str((self._time - 1) % 10))

        if self._queue:
            if self._queue[0].get_state() is CyclicTaskStates.FINISHED:
                del self._queue[0]
                self._remaining_quantum = self._quantum
            else:
                if self._remaining_quantum == 0:
                    self._queue.append(self._queue[0])
                    del self._queue[0]
                    self._remaining_quantum = self._quantum

    def execute(self):

        for task in self._tasks:
            self._history_dict[task.get_name()].append("-")

        if self._queue:
            try:
                self._queue[0].execute(self._time)
            except RuntimeError as e:
                self._error_list.append(str(e))
            self._history_dict[self._queue[0].get_name()][-1] = self._tasks_dict[self._queue[0].get_name()]
            self._remaining_quantum -= 1

        self._time += 1

    def play(self, how_much: int):
        for i in range(how_much):
            try:
                self.update()
            except RuntimeError as e:
                self._error_list.append(str(e))
            if self._error_list:
                break

    def print_timeline(self):
        print("Round Robin - RR (quantum = {})".format(self._quantum))
        self.show_tasks()
        if self._error_list:
            print("FAILED!")
            for msg in self._error_list:
                print("\t{}".format(msg))
        print("Timeline:")
        for task in self._tasks:
            print("{}:{}".format(self._history_dict[task.get_name()][0], "".join(self._history_dict[task.get_name()][1:])))
        print("{}:{}".format(self._timeline_channel[0], "".join(self._timeline_channel[1:])))
        print()

    def show_tasks(self):
        properties = ("start time", "period", "burst_time", "deadline")

        print("{: >10} {}".format("", 				" ".join("{: >10}".format(task.get_name()		) for task in self._tasks)))
        
        print("{: >10} {}".format(properties[0], 	" ".join("{: >10}".format(task.get_start_time()	) for task in self._tasks)))
        
        print("{: >10} {}".format(properties[1], 	" ".join("{: >10}".format(task.get_period()		) for task in self._tasks)))
        
        print("{: >10} {}".format(properties[2], 	" ".join("{: >10}".format(task.get_burst_time()	) for task in self._tasks)))
        
        print("{: >10} {}".format(properties[3], 	" ".join("{: >10}".format(task.get_deadline()	) for task in self._tasks)))
        
        print("")

def main():
    # taskn = CyclicTask( "tn", start_time, period, deadline, burst_time )
    task1 = CyclicTask("t1", 0, 16, 13, 10)
    task2 = CyclicTask("t2", 1, 16, 14, 4)
    task3 = CyclicTask("t3", 0, 24, 24, 4)
    task4 = CyclicTask("t4", 1, 30, 25, 3)
    edf = EarliestDeadlineFirstScheduler([task1, task2, task3, task4])
    try:
        edf.play(180)
    except RuntimeError as e:
        print(str(e))
    finally:
        edf.print_timeline()
		
    task1.reset_task()
    task2.reset_task()
    task3.reset_task()
    task4.reset_task()
    
    rr = RoundRobinScheduler(5, [task1, task2, task3, task4])
    try:
        rr.play(180)
    except RuntimeError as e:
        print(str(e))
    finally:
        rr.print_timeline()
    
    a = input("Press enter to end application")


if __name__ == '__main__':
    main()
