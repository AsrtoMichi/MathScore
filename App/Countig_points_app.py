#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
import json
import os


class App(tk.Tk):
    def __init__(self, solutions, n_competitors, vantage, derive, name):
        super().__init__()

        # starting main windows
        self.title("Competitors")
        self.geometry("800x300")

        # creations list solutions

        self.solutions = []
        for x in range(len(solutions)):
            partial = solutions[x]
            self.solutions.append([partial[0], partial[1], 0, 0, vantage])
        self.number_of_questions = len(self.solutions)

        # starting clock values

        self.total_time = 7200
        self.timer_seconds = self.total_time
        self.timer_status = 0

        # creations list points squadre

        self.n_competitors = n_competitors
        self.derive = derive

        self.base_points = 220
        self.svantage = 10

        self.list_point = []
        for _ in range(self.n_competitors):
            team_points = []
            for _ in range(self.number_of_questions):
                team_points.append([0, 0, 1])
            self.list_point.append(team_points)

        # reocrd list
        self.recording = []
        for _ in range(self.n_competitors):
            self.recording.append([(0, 220)])
        self.name = name

        self.create_widgets()

        self.arbiter_window()

    def arbiter_window(self):

        # starting artiter's window
        self.arbiter_GUI = tk.Toplevel(self)
        self.arbiter_GUI.title("Arbiter")
        self.arbiter_GUI.geometry("500x200")
        self.arbiter_GUI.resizable(False, False)

        # craatition entry for data

        squadre_label = tk.Label(self.arbiter_GUI, text="Team number:")
        squadre_label.pack()
        self.squadre_entry = tk.Entry(self.arbiter_GUI)
        self.squadre_entry.pack()

        question_label = tk.Label(self.arbiter_GUI, text="Question number:")
        question_label.pack()
        self.question_entry = tk.Entry(self.arbiter_GUI)
        self.question_entry.pack()

        value_label = tk.Label(self.arbiter_GUI, text="Insert an answer:")
        value_label.pack()
        self.answer_entry = tk.Entry(self.arbiter_GUI)
        self.answer_entry.pack()

        tk.Button(self.arbiter_GUI, text="Submit",
                  command=self.submit_answer).pack()

        self.jolly_window()

        self.arbiter_GUI.mainloop()

    def jolly_window(self):

        # starting jolly window
        self.jolly_GUI = tk.Toplevel(self)
        self.jolly_GUI.title("Jolly")
        self.jolly_GUI.geometry("500x200")
        self.jolly_GUI.register(False, False)

        # craatition entry for data

        squadre_label = tk.Label(self.jolly_GUI, text="Team number:")
        squadre_label.pack()
        self.squadre_entry_jolly = tk.Entry(self.jolly_GUI)
        self.squadre_entry_jolly.pack()

        question_label = tk.Label(self.jolly_GUI, text="Question number:")
        question_label.pack()
        self.question_entry_jolly = tk.Entry(self.jolly_GUI)
        self.question_entry_jolly.pack()

        tk.Button(self.jolly_GUI, text="Submit",
                  command=self.submit_jolly).pack()

        self.jolly_GUI.mainloop()

    def submit_answer(self):

        try:
            # get values
            selected_team = int(self.squadre_entry.get())
            entered_question = int(self.question_entry.get())
            entered_answer = float(self.answer_entry.get())

            # clear entry

            self.squadre_entry.delete(0, tk.END)
            self.question_entry.delete(0, tk.END)
            self.answer_entry.delete(0, tk.END)

            # get specif n_error and golly staus

            point_team = self.list_point[selected_team-1]
            errors, status, jolly = point_team[entered_question-1]

            # gestion error for fisic competions

            xm, er, correct, incorrect, points = self.solutions[entered_question - 1]
            ea = (er)/100*xm
            ma, mi = xm + ea, xm-ea

            # gestion gived solutiions

            if self.timer_status == 1:

                # if correct

                if mi <= entered_answer <= ma:
                    correct += 1
                    status = 1

                # if wrong

                elif entered_answer <= mi or entered_answer >= ma:
                    if status == 0:
                        errors += 1
                        incorrect += 1

            # inboxing solutions
            self.solutions[entered_question - 1] = [xm,
                                                    er, correct, incorrect, points]

            # inboxig points
            point_team[entered_question-1] = [errors, status, jolly]
            self.list_point[selected_team-1] = point_team
            self.update_entry()

            self.recording[selected_team-1].append(
                (self.total_time-self.timer_seconds, self.get_total_points(selected_team-1)))

        except ValueError:
            self.squadre_entry.delete(0, tk.END)
            self.question_entry.delete(0, tk.END)
            self.answer_entry.delete(0, tk.END)

        except IndexError:
            self.squadre_entry.delete(0, tk.END)
            self.question_entry.delete(0, tk.END)
            self.answer_entry.delete(0, tk.END)

    def submit_jolly(self):

        try:
            # get values

            selected_team = int(self.squadre_entry_jolly.get())
            entered_question = int(self.question_entry_jolly.get())

            # clear entry

            self.squadre_entry_jolly.delete(0, tk.END)
            self.question_entry_jolly.delete(0, tk.END)

            # check timer staus

            if self.timer_status == 1 and self.timer_seconds > (6600):

                # check if other jolly are been given
                if sum(sotto_lista[2] for sotto_lista in self.list_point[selected_team-1]) == self.number_of_questions:
                    # adding jolly

                    squadre_points = self.list_point[selected_team-1]
                    answer_squadre_points = squadre_points[entered_question-1]
                    answer_squadre_points[2] = 2
                    squadre_points[entered_question-1] = answer_squadre_points
                    self.list_point[selected_team-1] = squadre_points
        except ValueError:
            self.squadre_entry_jolly.delete(0, tk.END)
            self.question_entry_jolly.delete(0, tk.END)
        except IndexError:
            self.squadre_entry_jolly.delete(0, tk.END)
            self.question_entry_jolly.delete(0, tk.END)

    def point_answer(self, question):
        if question <= self.number_of_questions+1:
            answer_data = self.solutions[question-1]

            return answer_data[4]+answer_data[3]*2

    def get_point_answer(self, squadre, question):
        if question <= self.number_of_questions and squadre <= self.n_competitors:
            points_squadre = self.list_point[squadre-1]
            answer_point = points_squadre[question-1]

            return (answer_point[1]*self.point_answer(question)-answer_point[0]*self.svantage)*answer_point[2]

    def get_total_points(self, squadre):
        if squadre <= self.n_competitors:
            partial = []
            for x in range(self.number_of_questions):
                partial.append(self.get_point_answer(squadre, x))

            return sum(partial)+self.base_points

    def create_widgets(self):

        # cratin timer
        self.timer_label = tk.Label(self, text=f"Tempo rimasto: {self.timer_seconds // 3600:02}:{(
            self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}", font=("Helvetica", 18, "bold"))
        self.timer_label.pack()

        # cration start buttun
        self.start_button = tk.Button(
            self, text="Start", command=self.start_clock)
        self.start_button.pack()

        if self.timer_status == 1:
            self.start_button.config(state="disabled")

        # creation point label

        self.points_label = tk.Frame(self)
        self.points_label.pack(pady=20)

        # creations row, coluns

        for x in range(self.n_competitors+1):
            self.points_label.rowconfigure(x+1, weight=1)
            for y in range(self.number_of_questions):
                self.points_label.rowconfigure(y*2+2, weight=1)

        # creation label points value

        for z in range(self.number_of_questions):
            value_label = tk.Entry(self.points_label, width=5)
            value_label.insert(0, str(self.point_answer(z+1)))
            value_label.grid(column=z*2+3, row=0, sticky=tk.W)

        for x in range(1, self.n_competitors+1):

            tk.Label(self.points_label, text=f"Total {x}:", width=7).grid(
                column=0, row=x, sticky=tk.W)

            total_num = tk.Entry(self.points_label, width=5)
            total_num.insert(0, str(self.get_total_points(x)))
            total_num.grid(column=1, row=x, sticky=tk.W)

            for y in range(self.number_of_questions):
                # write number of question
                tk.Label(self.points_label, text=f"{y+1}", width=5).grid(
                    column=y*2+2, row=x, sticky=tk.W)

                point = self.get_point_answer(x, y+1)
                total_num = tk.Entry(self.points_label, width=5)
                total_num.insert(0, str(point))
                if point < 0:
                    total_num.configure(background="red")
                elif point > 0:
                    total_num.configure(background="green")
                else:
                    total_num.configure(background="white")
                total_num.grid(column=y*2+3, row=x, sticky=tk.W)

    def update_entry(self):
        self.timer_label.destroy()
        self.start_button.destroy()
        self.points_label.destroy()
        self.create_widgets()

    def update_timer(self):
        self.timer_seconds -= 1
        self.timer_label.config(text=f"Tempo rimasto: {self.timer_seconds // 3600:02}:{
                                (self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}")

        if self.timer_seconds > 0:

            self.after(1000, self.update_timer)

            if self.timer_seconds % 5 == 0:
                self.update_entry()

            if self.timer_seconds % 60 == 0:
                for x in range(self.number_of_questions):
                    answer = self.solutions[x]
                    if answer[2] < self.derive and self.timer_seconds <= 1800:
                        answer[4] += 1
                        self.update_entry()
                    self.solutions[x] = answer

        if self.timer_seconds == 0 and self.timer_status == 1:
            self.save_data(self.name, self.recording)
            self.timer_status == 2

    def save_data(self, name, data):

        with open(os.path.join(os.path.dirname(__file__), f"{name}.txt"), "w") as record:
            record.write(str(data))

    def start_clock(self):
        self.update_timer()
        self.update_entry()
        self.timer_status = 1
        self.start_button.config(state="disabled")


if __name__ == "__main__":

    file_path = os.path.join(os.path.dirname(__file__), "config.json")

    with open(file_path, 'r') as file:
        data = json.load(file)

    app = App(data['solutions'], data['squadre'],
              data['vantage'], data['derive'], data['name'])

    app.mainloop()
