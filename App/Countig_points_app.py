#!/usr/bin/env pypy3
# -*- coding: utf-8 -*-

from tkinter import Tk, Toplevel, Canvas, StringVar, Entry, Label
from tkinter.ttk import Frame, OptionMenu, Button, Scrollbar
from tkinter.messagebox import showerror
from json import load
from os import walk
from os.path import join, dirname
from typing import Union, List, Literal
from sys import exit


class File:
    @staticmethod
    def get_config() -> dict:
        try:
            file_path = join(dirname(__file__), "config.json")
            with open(file_path, 'r') as file:
                return load(file)
        except:
            showerror("Error", "unable to complete congfiguration")
            exit()

    @staticmethod
    def save_data(directory: str, name: str, data: dict):
        try:
            with open(join(directory, f"{name}.txt"), "w") as record:
                record.write(str(data))
        except:
            showerror(
                "Error", f"An error occurred:, data will be printed in the terminal.")
            print(data)

   
class Main(Tk):
    def __init__(self):
        # cration Main window

        super().__init__()
        self.title("Competitors")
        self.geometry(f"1850x630")
        self.resizable(False, False)

        # cration solutions

        data = File.get_config()
        self.solutions = {i+1: {"xm": solution,  "correct": 0, "incorrect": 0,
                                "value": data['vantage']} for i, solution in enumerate(data['solutions'])}
        self.number_of_questions = len(self.solutions)

        # genaration timer

        self.total_time = data['time']
        self.timer_seconds = self.total_time
        self.timer_status = 0

        # name team, base point, svantge, derive
        self.name_team =  data['squad']
        self.derive = data['derive']

        # data bot

        self.answer = date['answer']

        # list point, bonus, n_fulled

        self.list_point = {name: {question+1: {"errors": 0, "status": 0, "jolly": 1, "bonus": 0}
                                  for question in range(self.number_of_questions)} for name in self.name_team}
        for name in self.name_team:
            self.list_point[name]["base"] = [self.number_of_questions*10]

        self.fulled = 0

        # data recording
        self.recording = {name: [(0, 220)] for name in self.name_team}
        self.name = data['name']

        # creation clock

        self.directory_recording = data['directory_recording']
        self.timer_label = Label(self, text=f"Time left: {self.timer_seconds // 3600:02}:{(self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}", font=("Helvetica", 18, "bold"))
        self.timer_label.pack()
        self.start_button = Button(
            self, text="Start", command=self.start_clock)
        self.start_button.pack()


        points_label = Frame(self, width=1800, height=600)
        points_label.pack(pady=20)


        # Creazione del canvas all'interno dell'etichetta dei punti
        canvas = Canvas(points_label,  width=1800, height= 600)
        canvas.config(scrollregion=(0,0, 1800, len(self.name_team)*26))
        canvas.pack(side="left", expand=True, fill="both")

        # Aggiunta di una barra di scorrimento verticale
        scrollbar = Scrollbar(points_label, command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.config(yscrollcommand=scrollbar.set )

        self.frame_point = Frame(canvas, width=1800, height=len(self.name_team)*26)
        canvas.create_window((0, 0), window=self.frame_point, anchor='nw')

        # Creazione delle etichette per ogni domanda e riga
        for question in range(self.number_of_questions):
            for row in range(len(self.name_team)):
                # Numero della domanda
                index = Label(self.frame_point, text=f"{question+1}: ", width=3, anchor="e")
                index.grid(
                    column=question * 2 + 2, row=row + 1, sticky="ns")
                if row%2==0:
                    index.configure(background="#59D1FF")

        self.update_entry()

  

    def update_entry(self):
        for question in self.solutions.keys():
            value_label = Entry(self.frame_point, width=5)
            value_label.insert(0, str(self.point_answer(question)))
            value_label.grid(column=question*2+1, row=0, sticky="ns")
        index_frame = sorted([(self.total_squad_point(team), team)
                             for team in self.name_team], key=lambda x: x[0], reverse=True)
        

        for row, frame in enumerate(index_frame, 1):
            team = frame[1]
            name = Label(self.frame_point, text=f"{team}: ", anchor="e", width=15)
            name.grid(
                column=0, row=row, sticky="ns")
            if row%2==1:
                name.configure(background="#59D1FF")

            total_num = Entry(self.frame_point, width=5)

            total_num.insert(0, str(self.total_squad_point(team)))

            total_num.grid(column=1, row=row, sticky="ns")
            team_points = self.list_point[team]

            for column, question in enumerate(team_points.keys()-['base'], 1):

        
                total_num = Entry(self.frame_point, width=5)
                total_num.insert(0, self.point_answer_x_squad(team, question, True))
                
                if self.point_answer_x_squad(team, question) < 0:
                    total_num.configure(background="red")
                elif self.point_answer_x_squad(team, question) > 0:
                    total_num.configure(background="green")
                else:
                    total_num.configure(background="white")
                total_num.grid(column=column*2+1, row=row, sticky="ns")
        

    def start_clock(self):
        self.start_button.config(state="disabled")
        self.timer_status = 1
        self.update_timer()

    def update_timer(self):
        if self.timer_status == 1:

            if self.timer_seconds > 0:

                self.timer_seconds -= 1
                self.timer_label.config(text=f"Time left: {self.timer_seconds // 3600:02}:{(self.timer_seconds % 3600) // 60:02}:{self.timer_seconds % 60:02}")

                if self.timer_seconds % 60 == 0:

                    for question in self.solutions.keys():
                        answer = self.solutions[question]
                        if answer['correct'] < self.derive and self.timer_seconds >= 1200:
                            answer['value'] += 1
                        self.solutions[question] = answer

                    for answer in self.answer:
                        if answer['time'] == (self.total_time-self.timer_seconds)//60:
                            self.submit_answer(
                                answer['team'], answer['question'], answer['answer'])
                        else:
                            break

                    self.update_entry()

                self.after(1000, self.update_timer)

            elif self.timer_seconds == 0:
                File.save_data(self.directory_recording,
                               self.name, self.recording)
                self.timer_status = 2

    def submit_answer(self, selected_team: str, entered_question: int, entered_answer: int):

        if self.timer_status == 1:

            # get specif n_error and golly staus
            errors, status, jolly, bonus = self.list_point[selected_team][entered_question].values(
            )

            # gestion error for fisic competions
            xm,  correct, incorrect, value = self.solutions[entered_question].values(
            )

            # if correct
            if xm == entered_answer:
                correct += 1
                status = 1

                if 0 < correct < 5:
                    bonus = -5*correct+25
                elif correct == 5:
                    bonus = 3
                if sum([team['status'] for team in self.list_point[selected_team].values() if 'jolly' in team]) == self.number_of_questions:
                    self.fulled += 1
                    if self.fulled == 1:
                        self.list_point[selected_team]['base'] += 50
                    elif self.fulled == 2:
                        self.list_point[selected_team]['base'] += 30
                    elif self.fulled == 2:
                        self.list_point[selected_team]['base'] += 20
                    elif self.fulled == 2:
                        self.list_point[selected_team]['base'] += 15
                    elif self.fulled == 2:
                        self.list_point[selected_team]['base'] += 10

            # if wrong
            elif xm != entered_answer:
                if status == 0:
                    errors += 1
                    if errors == 1:
                        incorrect += 1

                # inboxing solutions
            self.solutions[entered_question] = {
                "xm": xm, "correct": correct, "incorrect": incorrect, "value": value}

            # inboxig points
            self.list_point[selected_team][entered_question] = {
                "errors": errors, "status": status, "jolly": jolly, "bonus": bonus}
            

            self.update_entry()

            self.recording[selected_team].append(
                (self.total_time-self.timer_seconds, self.total_squad_point(selected_team)))

    def submit_jolly(self, selected_team: str, entered_question: int):

        # check timer staus
        if self.timer_status == 1 and self.timer_seconds > (self.total_time-600):
            # check if other jolly are been given
            if sum([team['jolly'] for team in self.list_point[selected_team].values() if 'jolly' in team]) == self.number_of_questions:
                # adding jolly
                self.list_point[selected_team][entered_question]['jolly'] = 2
                self.update_entry()

    def point_answer(self, question: int) -> int:
        if question <= self.number_of_questions:
            answer_data = self.solutions[question]
            return int(answer_data['value'] + answer_data['incorrect'] * 2)

    def point_answer_x_squad(self, team: str, question: Union[str, int], jolly_simbol: bool = False) -> Union[int, str]:
        if team in self.name_team:
            points_squadre = self.list_point[team]
            if question == "base":
                return sum(points_squadre['base'])
            elif question <= self.number_of_questions:
                answer_point = points_squadre[question]
                output = ((answer_point['status'] * self.point_answer(question) -
                          answer_point['errors'] * 10+answer_point['bonus']) * answer_point['jolly'])
                return str(output) + " J" if answer_point['jolly'] == 2 and jolly_simbol else int(output)

    def total_squad_point(self, team: str) -> int:
        if team in self.name_team:
            return sum(self.point_answer_x_squad(team, question) for question in self.list_point[team].keys())


class Arbiter_GUI(Toplevel):

    def __init__(self, main):
        super().__init__(main)

        self.submit_answer_main = main.submit_answer
        self.name_team = main.name_team

        # starting artiter's window

        self.title("Arbiter")
        self.geometry("500x220")
        self.resizable(False, False)

        # craation entry for data

        Label(self, text="Team number:").pack()
        self.selected_team = StringVar()
        self.squadre_entry = OptionMenu(
            self, self.selected_team, *self.name_team[0], *self.name_team)
        self.selected_team.set("")
        self.squadre_entry.pack()

        Label(self, text="Question number:").pack()
        self.question_entry = Entry(self)
        self.question_entry.pack()

        Label(self, text="Insert an answer:").pack()
        self.answer_entry = Entry(self)
        self.answer_entry.pack()

        Button(self, text="Submit",
               command=self.submit_answer).pack(pady= 15)

    def submit_answer(self):
        try:

            self.submit_answer_main(
                self.selected_team.get(), int(self.question_entry.get()), int(self.answer_entry.get()))

        except:
            pass

        self.selected_team.set("")
        self.question_entry.delete(0, 'end')
        self.answer_entry.delete(0, 'end')


class Jolly_GUI(Toplevel):

    def __init__(self, main: classmethod):
        super().__init__(main)

        self.submit_jolly_main = main.submit_jolly
        self.name_team = main.name_team

        # starting jolly window
        self.title("Jolly")
        self.geometry("500x150")
        self.resizable(False, False)

        # creatition entry for data
        Label(self, text="Team number:").pack()
        self.selected_team_jolly = StringVar()
        self.squadre_entry_jolly = OptionMenu(
            self, self.selected_team_jolly,*self.name_team[0], *self.name_team)
        self.selected_team_jolly.set("")
        self.squadre_entry_jolly.pack()

        Label(self, text="Question number:").pack()
        self.question_entry_jolly = Entry(self)
        self.question_entry_jolly.pack()

        Button(self, text="Submit",
               command=self.submit_jolly).pack(pady=15)

    def submit_jolly(self):

        try:
            self.submit_jolly_main(self.selected_team_jolly.get(), int(
                self.question_entry_jolly.get()))

        except:
            pass
        self.selected_team_jolly.set("")
        self.question_entry_jolly.delete(0, 'end')


def main():
    root = Main()
    arbiter = Arbiter_GUI(root)
    jolly = Jolly_GUI(root)
    del root, arbiter

    jolly.mainloop()


if __name__ == "__main__":
    main()
