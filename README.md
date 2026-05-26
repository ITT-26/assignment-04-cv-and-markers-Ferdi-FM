[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/5NorvP5a)

# Starting a Script/Game:

## Requirements
- Python3

## Initializing and starting Virtual Enviroment

### For Windows
Open The Root-Directory (Assignment-02-...) in a Terminal and create + activate the virtual enviroment with:
````
py -m venv venv
venv\Scripts\activate
````
(venv) should now be displayed before your new CommandLine in the Terminal

Next install the requirements:
````
pip install -r requirements.txt
````

Then open the desired file,
For [Perspektive Transformation](#Perspective-Transformation):
````
py perspective_transformation\image_extractor.py
````
For [AR-Game](#AR-Game-Ballon-Game):
````
py ar_game\AR_game.py
````
### For Mac
The Steps are the same, but the concrete commands different:
````
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 perspective_transformation\opencv_click.py
python3 ar_game\opencv_pyglet.py
````
<br><br>

# Perspective Transformation
1. Start the script with parameters, e.g
    ````
    py perspective_transformation\image_extractor.py --input_path example.jpg --output_path transformed\transformed_example.jpg --width 530 --height 350
    ````

    - You can either give an output_path with filename or just the path to a directory, in that case it will be saved as "transformed_image_X" where x is the number of already saved transformed_images
    - if either path if wrong, a filedialog will open prompting you to select a valid path (It wont create the directory because little typos could possibly create a bunch of unwanted folders)
    - if width/height are ommited they will be the size of the selected rectangle
    - if you quit out of either dialog the script will exit
    
    Additionally all arguments are optional, so you can also just start by typing:
    ````
    py perspective_transformation\image_extractor.py
    ````
    then a fileDialog for the file to open and a saveFiledialog for the savepath will open, width and height will be the size of the selected rectangle

2. Click on the 4 Points you want to transform into an even rectangle
3. If your unhappy press *__"ESC"__* to restart or keep clicking in the image to change the points (if you would add a fifth point the first one is deletet and replaced by the new point)
4. Once your happy press *__"S"__* to save the transformed image
5. press __"Q"__ to exit

<br><br>

# AR-Game (Ballon Game)
1. Start the script
    ````
    py ar_game\AR_game.py
    ````
2. The Game only starts once the four corners of the playingfield are detected and pauses if interupted\
Make sure you got the playing-field the right way round!
3. I recommend either indirect lighting or bright white light
4. Game:
    - 4 Ballons will float up/down, your job is to keep them afloat for as long as possible
    - The ballons have random acceleration and width
    - Use a _finger_ to keep them up
    - Easy:\
        Game Over when all ballons are outofbounds at the bottom (really easy)
    - Hard:\
        Game Over when one ballon is outofbounds at the bottom
    - For the best experience keep your finger close to the playing field
    - **Don't cheat by using your whole hand!**
5. Have Fun!