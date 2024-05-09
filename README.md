![Font](https://github.com/AsrtoMichi/MathScore/assets/146475341/5a9a03e5-f449-4fc1-b5a7-84d55af7ac5b)
# Introduction
This app is aimed at counting points in math and physics competitions.
The app consists of three windows: one for viewing the scores, one for entering the results, and one for entering the jolly (only one for team).  
It also saves all variations of the total points and saves that in a .txt file in the same directory, to make grafic read above.

# Functionality

## Pdf anlysis
The program is capable of analyzing PDFs to extract:
- questions' answers;
- answers given by the team during the match.

## Grafic
It is possible to create a graphic whit that data with [Graphic.py](https://github.com/AsrtoMichi/MathScore/tree/Grafic). 
App for work needs to have the recording (name.txt) file in their same directory.

# Configuration
- Is requred [pypdf](https://pypi.org/project/pypdf/);
  - to install use command `pip install pypdf`;
  - the analysis of PDFs is limited to those coming from the site [PHI Quadro](https://www.phiquadro.it/index.php);
- configure the .ini properly, **is necessary**;
  - there is no difference between phat with `C:\\` and `c:\\`.

## Credit
This app is app is inspired by [PHI Quadro](https://www.phiquadro.it/index.php).
