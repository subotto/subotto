//#include <SimpleTimer.h>

#define BLUE1_PIN 4
#define BLUE2_PIN 4
#define RED1_PIN 7
#define RED2_PIN 7

#define BLUE1_GOAL 1
#define BLUE2_GOAL 2
#define RED1_GOAL 3
#define RED2_GOAL 4

#define BLUE_ADD_PIN 8
#define BLUE_UNDO_PIN 9
#define RED_ADD_PIN 10
#define RED_UNDO_PIN 11

#define BLUE_ADD_PUSH 5
#define BLUE_UNDO_PUSH 6
#define RED_ADD_PUSH 7
#define RED_UNDO_PUSH 8


#define TEST_MODE 0
#define SLAVE_MODE 1

#define GOAL_DELAY 3000
#define PUSH_DELAY 5000

int mode;
unsigned long last_goal;
unsigned long last_push;
//int sensors_enabled;

//SimpleTimer timer;

void setup()
{
  pinMode(BLUE1_PIN,INPUT);
  pinMode(BLUE2_PIN,INPUT);
  pinMode(RED1_PIN,INPUT);
  pinMode(RED2_PIN,INPUT);
  
  pinMode(BLUE_ADD_PIN,INPUT_PULLUP);
  pinMode(BLUE_UNDO_PIN,INPUT_PULLUP);
  pinMode(RED_ADD_PIN,INPUT_PULLUP);
  pinMode(RED_UNDO_PIN,INPUT_PULLUP);
  
  
  
  pinMode(13,OUTPUT);
  digitalWrite(13,LOW);
  
  Serial.begin(9600);
  
  mode = TEST_MODE;
//  last_goal = millis();
//  last_push = millis();
  last_goal = 0;
  last_push = 0;
//  sensors_enabled = 1;
  
}

void loop()
{
  int input = -1;
  if (Serial.available()>0)
  {
    // Comunicazione in arrivo dal master
    
    input = Serial.parseInt();
//    Serial.println(input);
    if (input == 0)
    {
      mode = TEST_MODE;
      input = -1;
    }
    else if (input == 16)
    {
      mode = SLAVE_MODE;
      input = -1;
    }
  }
  if (mode == TEST_MODE)
    test_main(input);
  else if (mode == SLAVE_MODE)
    slave_main(input);  
  
  
  
}

void test_main(int input)
{
  int result = -1;
  if (input == 1)
    result = digitalRead(BLUE1_PIN);
  else if (input == 2)
    result = digitalRead(BLUE2_PIN);
  else if (input == 3)
    result = digitalRead(RED1_PIN);
  else if (input == 4)
    result = digitalRead(RED2_PIN);
  
  if (result != -1)
    Serial.println(result);
  
}




void slave_main(int input)
{
//  Serial.println("Begin slave main");
  if (millis() > last_goal + GOAL_DELAY)
//  if (sensors_enabled)
  {
     if (digitalRead(BLUE1_PIN))
     {
       Serial.println(BLUE1_GOAL);
       last_goal = millis();
//       while(digitalRead(BLUE1));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);
     }
     if (digitalRead(BLUE2_PIN))
     {
       Serial.println(BLUE2_GOAL);
       last_goal = millis();
//       while(digitalRead(BLUE2));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);

     }
     if (digitalRead(RED1_PIN))
     {
       Serial.println(RED1_GOAL);
       last_goal = millis();
//       while(digitalRead(RED1));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);


     }
     if (digitalRead(RED2_PIN))
     {
       Serial.println(RED2_GOAL);
       last_goal = millis();
//       while(digitalRead(RED2));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);
     }
    
  }
//  else
//    Serial.println("not_enable");

//  if (millis() > last_push + PUSH_DELAY)
  if (0 == 1)
  {
    if (digitalRead(BLUE_ADD_PIN))
    {
       Serial.println(BLUE_ADD_PUSH);
       last_push = millis();
    }
    if (digitalRead(BLUE_UNDO_PIN))
    {
       Serial.println(BLUE_UNDO_PUSH);
       last_push = millis();
    }
    if (digitalRead(RED_ADD_PIN))
    {
       Serial.println(RED_ADD_PUSH);
       last_push = millis();
    }
    if (digitalRead(RED_UNDO_PIN))
    {
       Serial.println(RED_UNDO_PUSH);
       last_push = millis();
    }
  }
  
}

/*void enable_sensors()
{
  Serial.println("enable");
  sensors_enabled = 1;
}*/
