#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Competitors")
        self.geometry("1500x300")
        self.n_concorrenti = 3
        self.punteggio_base = [220, 0]
        self.vantage = 100
        self.svantage = 10
        self.solutions = ((3.16503, 4, self.vantage), (3.06212, 1, self.vantage), (3.39618, 0.5, self.vantage), (411.88751, 0.5, self.vantage), (4769.40195, 0.5, self.vantage), (0.06250, 0.5, self.vantage), (75.90132, 0.5, self.vantage), (8.94196, 0.5, self.vantage),
                          (1.02031, 0.5, self.vantage), (1.17150, 0.5, self.vantage), (0.80000, 0.5, self.vantage), (56276.60708, 0.5, self.vantage), (4.22022, 0.5, self.vantage), (0.33356, 0.5, self.vantage), (1413.03770, 0.5, self.vantage), (0.76749, 0.5, self.vantage))
        self.number_of_questions = len(self.solutions)
        self.timer_seconds = 7200
        self.timer_status = 0
        self.list_point = []
        for x in range(self.n_concorrenti):
            team_points = [self.punteggio_base]
            for _ in range(self.number_of_questions):
                team_points.append([0, 1])
            self.list_point.append(team_points)

        self.create_widgets()
        self.arbiter_window()

    def arbiter_window(self):
        self.arbiter_GUI = tk.Toplevel(self)
        self.arbiter_GUI.title("Arbiter")
        self.arbiter_GUI.geometry("500x200")

        squadre_label = tk.Label(
            self.arbiter_GUI, text="Team number:")
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
                  command=self.submit_values).pack()

        self.jolly_window()

        self.arbiter_GUI.mainloop()

    def jolly_window(self):
        self.jolly_GUI = tk.Toplevel(self)
        self.jolly_GUI.title("Jolly")
        self.jolly_GUI.geometry("500x200")

        squadre_label = tk.Label(
            self.jolly_GUI, text="Team numbe:")
        squadre_label.pack()
        self.squadre_entry_jolly = tk.Entry(self.jolly_GUI)
        self.squadre_entry_jolly.pack()

        question_label = tk.Label(self.jolly_GUI, text="Question number:")
        question_label.pack()
        self.question_entry_jolly = tk.Entry(self.jolly_GUI)
        self.question_entry_jolly.pack()

        tk.Button(self.jolly_GUI, text="Submit",
                  command=self.submit_values2).pack()

        self.jolly_GUI.mainloop()

    def submit_values(self):
        selected_team = int(self.squadre_entry.get())
        entered_question = int(self.question_entry.get())
        entered_answer = float(self.answer_entry.get())

        xm, er, points = self.solutions[entered_question - 1]

        ea = (er)/100*xm

        ma, mi = xm + ea, xm-ea

        if self.timer_status == 1:

            point_team = self.list_point[selected_team-1]

            answer_point_team = point_team[entered_question]

            base_point, jolly = answer_point_team

            if mi <= entered_answer <= ma:
                base_point += jolly * points
                jolly = 0

            elif entered_answer <= mi or entered_answer >= ma:
                if entered_answer is not None:

                    base_point -= self.svantage*jolly

            point_team[entered_question] = [base_point, jolly]

            self.list_point[selected_team-1] = point_team
        self.update_entry()

    def submit_values2(self):
        selected_team = int(self.squadre_entry_jolly.get())
        entered_question = int(self.question_entry_jolly.get())
        if self.timer_status == 1 and self.timer_seconds > (6600):
            if sum(sotto_lista[1] for sotto_lista in self.list_point[selected_team-1]) == self.number_of_questions:
                squadre_points = self.list_point[selected_team-1]
                answer_squadre_points = squadre_points[entered_question]
                answer_squadre_points[1] = 2
                squadre_points[entered_question] = answer_squadre_points
                self.list_point[selected_team-1]
            squadre_points

    def create_widgets(self):
        self.timer_label = tk.Label(self, text=f"Tempo rimasto: {self.timer_seconds // 3600:02}:{(
            self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}", font=("Helvetica", 18, "bold"))
        self.timer_label.pack()
        self.start_button = tk.Button(
            self, text="Start", command=self.start_clock)
        self.start_button.pack()
        self.add_entry_points()

    def add_entry_points(self):
        self.list_frame = []
        for x in range(self.n_concorrenti):

            frame = tk.Frame(self)
            squadre_points = self.list_point[x]

            tk.Label(frame, text="Total:").pack(side="left", padx=5)
            entry_total = tk.Entry(frame, width=5)
            entry_total.insert(0, f"{sum(sotto_lista[0]
                                         for sotto_lista in self.list_point[x])}")
            entry_total.pack(side="left", padx=5)

            for y in range(self.number_of_questions):
                answer_squadre_points = squadre_points[y+1]
                tk.Label(frame, text=f"{y+1}:").pack(side="left", padx=5)
                entry = tk.Entry(frame, width=5)
                entry.insert(0, f"{answer_squadre_points[0]}")
                if answer_squadre_points[0] < 0:
                    entry.config(bg="red")
                elif answer_squadre_points[0] > 0:
                    entry.config(bg="green")
                entry.pack(side="left", padx=3)

            self.list_frame.append(frame)
            frame.pack()

    def update_entry(self):
        self.timer_label.destroy()
        self.start_button.destroy()
        for x in range(len(self.list_frame)):
            self.list_frame[x].destroy()
        self.create_widgets()

    def update_timer(self):
        self.timer_seconds -= 1
        self.timer_label.config(text=f"Tempo rimasto: {self.timer_seconds // 3600:02}:{
                                (self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}")
        if self.timer_seconds > 0:
            self.after(1000, self.update_timer)
        else:
            self.timer_status = 0

    def start_clock(self):
        self.update_timer()
        self.timer_status = 1


if __name__ == "__main__":
    app = App()

    app.mainloop()
