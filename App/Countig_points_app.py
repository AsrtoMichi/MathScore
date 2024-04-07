#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import tkinter as tk
import json
import os
from typing import Union


class File:
    @staticmethod
    def get_config():
        file_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(file_path, 'r') as file:
            return json.load(file)

    @staticmethod
    def save_data(name, data: list):
        with open(os.path.join(os.path.dirname(__file__), f"{name}.txt"), "w") as record:
            record.write(str(data))


class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Competitors")
        self.geometry("800x300")
        data = File.get_config()
        self.solutions = {i+1: {"xm": solution[0], "er": solution[1], "correct": 0, "incorrect": 0,
                                "value": data['vantage']} for i, solution in enumerate(data['solutions'])}
        self.number_of_questions = len(self.solutions)
        base_points = self.number_of_questions*10
        self.svantage = 10
        self.derive = data['derive']
        self.total_time = 7200
        self.timer_seconds = self.total_time
        self.timer_status = 0
        self.name_team =  data['squad']
        self.n_competitors = len(self.name_team)
        self.list_point = {name: {question+1: {"errors": 0, "status": 0, "jolly": 1, "bonus": 0}
                                  for question in range(self.number_of_questions)} for name in self.name_team}
        for name in self.name_team:
            self.list_point[name]["base"] = [base_points]
        self.fulled = 0
        self.recording = {name: [(0, 220)] for name in self.name_team}
        self.name = data['name']
        self.timer_label = tk.Label(self, text=f"Time left: {self.timer_seconds // 3600:02}:{(
            self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}", font=("Helvetica", 18, "bold"))
        self.timer_label.pack()
        self.start_button = tk.Button(
            self, text="Start", command=self.start_clock)
        self.start_button.pack()
        self.points_label = tk.Frame(self)
        self.points_label.pack(pady=20)
        for x in range(self.n_competitors + 1):
            self.points_label.rowconfigure(x + 1, weight=1)
        for y in range(self.number_of_questions):
            self.points_label.rowconfigure(y * 2 + 2, weight=1)
        for question in self.solutions.keys():
            self.value_label = tk.Entry(self.points_label, width=5)
            self.value_label.insert(0, str(self.point_answer(question)))
            self.value_label.grid(column=question*2+3, row=0, sticky=tk.W)
        index_frame = sorted([(self.total_squad_point(team), team)
                             for team in self.name_team], key=lambda x: x[0], reverse=True)
        row = 1
        for frame in index_frame:
            team = frame[1]
            tk.Label(self.points_label, text=f"Team {team}:", width=7).grid(
                column=0, row=row, sticky=tk.W)
            self.total_num = tk.Entry(self.points_label, width=5)
            self.total_num.insert(0, str(self.total_squad_point(team)))
            self.total_num.grid(column=1, row=row, sticky=tk.W)
            team_points = self.list_point[team]
            for question in team_points.keys()-['base']:
                tk.Label(self.points_label, text=f"{question}:   ", width=5, anchor="e").grid(
                    column=question*2+2, row=row, sticky=tk.W)
                self.total_num = tk.Entry(self.points_label, width=5)
                self.total_num.insert(
                    0, self.point_answer_x_squad(team, question, True))
                if self.point_answer_x_squad(team, question) < 0:
                    self.total_num.configure(background="red")
                elif self.point_answer_x_squad(team, question) > 0:
                    self.total_num.configure(background="green")
                else:
                    self.total_num.configure(background="white")
                self.total_num.grid(column=question*2+3, row=row, sticky=tk.W)
            row += 1

    def update_entry(self):
        for question in self.solutions.keys():
            self.value_label = tk.Entry(self.points_label, width=5)
            self.value_label.insert(0, str(self.point_answer(question)))
            self.value_label.grid(column=question*2+3, row=0, sticky=tk.W)
        index_frame = sorted([(self.total_squad_point(team), team)
                             for team in self.name_team], key=lambda x: x[0], reverse=True)
        row = 1
        for frame in index_frame:
            team = frame[1]
            tk.Label(self.points_label, text=f"Team {team}:", width=7).grid(
                column=0, row=row, sticky=tk.W)
            total_num = tk.Entry(self.points_label, width=5)
            total_num.insert(0, str(self.total_squad_point(team)))
            total_num.grid(column=1, row=row, sticky=tk.W)
            team_points = self.list_point[team]
            for question in team_points.keys()-['base']:
                self.total_num = tk.Entry(self.points_label, width=5)
                self.total_num.insert(
                    0, self.point_answer_x_squad(team, question, True))
                if self.point_answer_x_squad(team, question) < 0:
                    self.total_num.configure(background="red")
                elif self.point_answer_x_squad(team, question) > 0:
                    self.total_num.configure(background="green")
                else:
                    self.total_num.configure(background="white")
                self.total_num.grid(column=question*2+3, row=row, sticky=tk.W)
            row += 1

    def update_timer(self):
        self.timer_seconds -= 1
        self.timer_label.config(text=f"Time left: {self.timer_seconds // 3600:02}:{
                                (self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}")
        if self.timer_seconds > 0:
            self.after(1000, self.update_timer)
            if self.timer_seconds % 60 == 0:
                for question in self.solutions.keys():
                    answer = self.solutions[question]
                    if answer['correct'] < self.derive and self.timer_seconds >= 1200:
                        answer['value'] += 1
                    self.solutions[question] = answer
                    self.update_entry()
        if self.timer_seconds == 0 and self.timer_status == 1:
            File.save_data(self.name, self.recording)
            self.timer_status == 2

    def start_clock(self):
        self.update_timer()
        self.update_entry()
        self.timer_status = 1
        self.start_button.config(state="disabled")

    def point_answer(self, question: int):
        if question <= self.number_of_questions:
            answer_data = self.solutions[question]
            return int(answer_data['value'] + answer_data['incorrect'] * 2)

    def point_answer_x_squad(self, team: str, question: Union[str, int], jolly_simbol: bool = False):
        if team in self.name_team:
            points_squadre = self.list_point[team]
            if question == "base":
                return sum(points_squadre['base'])
            elif question <= self.number_of_questions:
                answer_point = points_squadre[question]
                output = ((answer_point['status'] * self.point_answer(question) -
                          answer_point['errors'] * self.svantage+answer_point['bonus']) * answer_point['jolly'])
                return str(output) + " J" if answer_point['jolly'] == 2 and jolly_simbol else int(output)

    def total_squad_point(self, team: str):
        if team in self.name_team:
            return sum(self.point_answer_x_squad(team, question) for question in self.list_point[team].keys())


class Arbiter_GUI(tk.Toplevel):

    def __init__(self, main):
        super().__init__(main)

        self.main = main

        # starting artiter's window

        self.title("Arbiter")
        self.geometry("500x200")
        self.resizable(False, False)

        # craation entry for data

        tk.Label(self, text="Team number:").pack()
        self.selected_team = tk.StringVar()
        self.squadre_entry = tk.OptionMenu(
            self, self.selected_team, *self.main.name_team)
        self.squadre_entry.pack()

        tk.Label(self, text="Question number:").pack()
        self.question_entry = tk.Entry(self)
        self.question_entry.pack()

        tk.Label(self, text="Insert an answer:").pack()
        self.answer_entry = tk.Entry(self)
        self.answer_entry.pack()

        tk.Button(self, text="Submit",
                  command=self.submit_answer).pack()

    def submit_answer(self):
        try:
            if self.main.timer_status == 1:
                # get values
                selected_team = self.selected_team.get()
                entered_question = int(self.question_entry.get())
                entered_answer = float(self.answer_entry.get())

                # clear entry
                self.selected_team.set(0)
                self.question_entry.delete(0, tk.END)
                self.answer_entry.delete(0, tk.END)

                # get specif n_error and golly staus
                point_team = self.main.list_point[selected_team]
                errors, status, jolly, bonus = point_team[entered_question].values(
                )

                # gestion error for fisic competions
                xm, er, correct, incorrect, value = self.main.solutions[entered_question].values(
                )
                ea = (er)/100*xm
                ma, mi = xm + ea, xm-ea

                # gestion given solutiions

                # if correct
                if mi <= entered_answer <= ma and status == 0:
                    correct += 1
                    status = 1

                    if 0 < correct < 5:
                        bonus = -5*correct+25
                    elif correct == 5:
                        bonus = 3
                    if sum([team['status'] for team in self.main.list_point[selected_team].values() if 'jolly' in team]) == self.main.number_of_questions:
                        self.main.fulled += 1
                        if self.main.fulled == 1:
                            point_team['base'] += 50
                        elif self.main.fulled == 2:
                            point_team['base'] += 30
                        elif self.main.fulled == 2:
                            point_team['base'] += 20
                        elif self.main.fulled == 2:
                            point_team['base'] += 15
                        elif self.main.fulled == 2:
                            point_team['base'] += 10
                # if wrong
                elif entered_answer <= mi or entered_answer >= ma:
                    if status == 0:
                        errors += 1
                        if errors == 1:
                            incorrect += 1

                # inboxing solutions
                self.main.solutions[entered_question] = {
                    "xm": xm, "er": er, "correct": correct, "incorrect": incorrect, "value": value}

                # inboxig points
                point_team[entered_question] = {
                    "errors": errors, "status": status, "jolly": jolly, "bonus": bonus}

                self.main.list_point[selected_team] = point_team

                self.main.update_entry()

                self.main.recording[selected_team].append(
                    (self.main.total_time-self.main.timer_seconds, self.main.total_squad_point(selected_team)))

        except:
            self.selected_team.set(0)
            self.question_entry.delete(0, tk.END)
            self.answer_entry.delete(0, tk.END)


class Jolly_GUI(tk.Toplevel):

    def __init__(self, main: classmethod):
        super().__init__(main)

        self.main = main

        # starting jolly window
        self.title("Jolly")
        self.geometry("500x200")
        self.resizable(False, False)

        # creatition entry for data
        tk.Label(self, text="Team number:").pack()
        self.selected_team_jolly = tk.StringVar()
        self.squadre_entry_jolly = tk.OptionMenu(
            self, self.selected_team_jolly, *self.main.name_team)
        self.squadre_entry_jolly.pack()

        tk.Label(self, text="Question number:").pack()
        self.question_entry_jolly = tk.Entry(self)
        self.question_entry_jolly.pack()

        tk.Button(self, text="Submit",
                  command=self.submit_jolly).pack()

    def submit_jolly(self):

        try:
            # get values
            selected_team = self.selected_team_jolly.get()
            entered_question = int(self.question_entry_jolly.get())

            # clear entry
            self.selected_team_jolly.set(0)
            self.question_entry_jolly.delete(0, tk.END)

            # check timer staus
            if self.main.timer_status == 1 and self.main.timer_seconds > (6600):

                # check if other jolly are been given
                if sum([team['jolly'] for team in self.main.list_point[selected_team].values() if 'jolly' in team]) == self.main.number_of_questions:
                    # adding jolly
                    squadre_points = self.main.list_point[selected_team]
                    answer_squadre_points = squadre_points[entered_question]
                    answer_squadre_points['jolly'] = 2
                    squadre_points[entered_question] = answer_squadre_points
                    self.main.list_point[selected_team] = squadre_points
                    self.main.update_entry()
        except:
            self.selected_team_jolly.set(0)
            self.question_entry_jolly.delete(0, tk.END)


if __name__ == "__main__":

    root = Main()
    arbiter = Arbiter_GUI(root)
    jolly = Jolly_GUI(root)

    jolly.mainloop()
