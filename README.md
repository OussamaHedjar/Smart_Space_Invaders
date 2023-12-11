# Smart-Space-Invaders
Smart Space Invaders is a retro game of one of the most successful arcade games in history, which is Space Invaders, in this change, we hope our intention of adding the element of machine learning to be widely stated.
The goal of this project is to learn and apply the knowledge gained to add more features than the original game had, as the original was only played on an endless loop. However, the smart space invaders had implemented many more, the most important ones were:

• Level Mode.

• Multiplayer Mode.

• A replica of the original’s Infinite Mode.

• Web service.

• Machine Learning.


The game is built using Python as the programming language because we saw its flexibility and the broad online community behind it, and we focused on the use of three important libraries:
● Pygame.

● Django.

● Tensorflow.

Pygame helped us in animation where it included computer graphics and sound
libraries, and Django high-level Python web framework that enables rapid development
of secure and maintainable websites specialized in back-end development, and
Tensorflow helped in computations regarding making machine learning and Neural Network
(NN) faster.
An overlook on the implemented features:
# Level Mode:
This mode is designed with the idea of challenging the player’s skills. The player who wishes to finish this mode will play 10 levels to accomplish that. Each level is constructed by:
•	Finite number of ships.
•	Random positions for each level and game.
•	Random speed for each level and game.
The finite number of ships
Starting with the first level, which has 4 ships, each leveling up will add 3 extra ships to the next level, this will lead to the player who’s playing the 10th  level (the last in the game) facing a total of 30 ships.
Random positioning
To keep the game fun and mysterious. We decided that the positions of the enemies should be anonymous at every level and every game to keep the challenge alive every time the player plays.
We made every time level initialized with random coordinates for every ship, this did prove to be a challenge especially when it came to making sure that no two ships overlapped.



### Random speed
In addition to the random positioning, we added another challenge to the player, we had the idea of implementing in every level a random speed for every ship, which also posed a challenge to us, as controlling every ship with its speed was difficult, we decided to move the ships as a unit, which proved to be controllable and also made our goal achievable.  

# Multiplayer Mode
With this mode, we decided to go with the classic split-screen local 1v1 (player vs player)  that you might see in the classic arcade centers or the ones you remember from your childhood, to create a competitive nostalgic atmosphere for the players as they try their hardest to defeat the opposing player next to them and claim victory.
Each player has a spaceship that can move (up, down, left, right) and each player has a health counter that gets reduced by 1 each time the spaceship is hit by a bullet, so the health counter must be kept above 0 at all costs to avoid imminent destruction.
The spaceship and health counter are located either on the left or right of the screen to each respective player, and of course, don’t forget that every spaceship has to come with a set of fully loaded guns! to strike down the other player and be.


# Infinite Mode
A level implemented mainly for game-playing AI. In this level, the aliens respawn in a random location every time they are hit, and game over only occurs when player lives are consumed.
Alien movements are mostly random. The goal is to create an easy environment where we can gather dataset samples. If the model learns to play this level well, we can then teach the model to play other levels with ease. Later, we decided to keep it as a tribute to the original game.

# Machine Learning
For the AI aspect of this project, we used a Convolutional Neural Network (CNN) to create an image recognition model.
Usually when creating an AI model to play a certain game, the game is simulated first to acquire data about the state of the game.
For example, in real-time fast-paced shooter games, a projectile may not hit until a few milliseconds after shooting it. So, when shooting multiple projectiles for example, it becomes difficult to determine what projectile hit, without accessing or simulating the game to get accurate data, which is typically not available to players except through the screen.
Our approach was to try to eliminate the need for simulating games, and training AI models using only visual representations of the data through image classification algorithms.
To create a game-playing AI model that can successfully navigate and learn the game, we needed to create a model that extracts any hidden patterns and strategies that good players use consciously and subconsciously. To be able to create such a model, we needed to first gather a dataset, train the model to find optimized parameters, then finally test the model. This process was repeated multiple times to achieve our desired models. Our models were built with four things in mind:
•	Dataset
•	Training
•	Implementation
•	Results

### The Dataset
●	Images are screen-captured automatically.
  - 187,000 data samples, 46,500 for each label.
  - Labels are shoot, left, right, and no move.
  - Smaller (6,800) manually labeled datasets for testing.
●	Preprocessing.
  - Cropping		- Resizing	- Data cleaning (special cases and errors)
•	Augmentation.
  - Theoretically, we can double our dataset size by flipping

### Training
•	Tools
  - Tensorflow, Google Collab, GPU
•	Architectures
  - AlexNet, MobileNet, EfficientNet, VGG, ResNet and custom architectures.
•	Methodology
  - Testing architecture, training, and setting early stop conditions.
•	Limitations & Setbacks
  - Google Collab producing unwanted results.
  - Insufficient metrics (i.e. cannot measure playing ability directly).
Implementation
•	Prediction
  - During the main game loop.
  - Threading to prevent prediction delay from affecting the game.
  - Last In First Out queue to handle screen captures, while keeping consistency and avoiding race conditions.
    
•	Playing
  - MOVE_SET = [0, 0, 0] # [left, shoot, right]
    
The same move is kept until the next prediction overwrites it.
•	Optimization
  - Control predictions per second.
  - Control thread wait time (to ensure only the most recent screenshot is used).
    
### Results
•	Model issues
  - Most models produced generate random or skewed predictions outside the validation dataset, most likely due to overfitting.
  - This was solved by introducing early stopping, and also by re-training the model until model/architecture is accepted or rejected.
  - Accuracy and validation accuracy are mostly irrelevant as a metric for our implementation.
  - Models that can navigate the game and track aliens cannot detect the small projectiles that the aliens shoot.
•	Accuracy
  - Ranging from 72 to 88 validation accuracy on good playing models.
•	Game playing
  - Approximately 150 models were produced in total, and 30 models were tested in-game.
  - Around 5% of total produced models were able to play the game in a way that does not seem random.
  - On average, the best-performing model can get around 300 scores, this is mainly because the alien cannot correctly perceive the alien projectiles.
•	Conclusion
  - Below-average playing AI model with current dataset size.
  - Need further testing with a larger dataset.
  - More robust screen and input capturing.

    
# Web service
Our website is developed and designed using a popular framework called Django.
Our website is hosted on the popular hosting service Heroku, which provided us with all the necessary tools for publishing the website and creating and managing the database.


# Future work
Game-playing AI
- Significantly improve the AI model scores.
- Prompt users to help us improve our AI with their gameplay recordings.
- Design a system to easily apply our design to make similar game-playing AIs for other games.
Game
- Add online multiplayer modes in addition to 1 vs 1.
- Improve menu design and functions and adding more options such as changing the resolution and more customization.
- Further improvements in performance and stability
Web services
- Add friends list, challenges, online forums, chat functions, and other sign-in and authentication options such as Google, Twitter, etc.…
- Add a feedback section so we can gather information on what to improve.
  
This project was conducted at King Saud University, and it holds all copyrights for it.
## Developed by:
### Oussama Hedjar.
### Abdulaziz Alsharif.     
### Ammar Alamri.          
### Ibrahim Almuharib.   
## Supervised by:
### Prof.Khalil El Hindi

