//#include <SimpleTimer.h>

#include "opcodes.h"

#define BLUE1_PIN 4
#define BLUE2_PIN 4
#define RED1_PIN 7
#define RED2_PIN 7

//#define BLUE1_GOAL 1
//#define BLUE2_GOAL 2
//#define RED1_GOAL 3
//#define RED2_GOAL 4

#define BLUE_ADD_PIN 8
#define BLUE_UNDO_PIN 9
#define RED_ADD_PIN 10
#define RED_UNDO_PIN 11

//#define BLUE_ADD_PUSH 5
//#define BLUE_UNDO_PUSH 6
//#define RED_ADD_PUSH 7
//#define RED_UNDO_PUSH 8


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
  pinMode(BLUE1_PIN,INPUT_PULLUP);
  pinMode(BLUE2_PIN,INPUT_PULLUP);
  pinMode(RED1_PIN,INPUT_PULLUP);
  pinMode(RED2_PIN,INPUT_PULLUP);
  
  pinMode(BLUE_ADD_PIN,INPUT_PULLUP);
  pinMode(BLUE_UNDO_PIN,INPUT_PULLUP);
  pinMode(RED_ADD_PIN,INPUT_PULLUP);
  pinMode(RED_UNDO_PIN,INPUT_PULLUP);
  
  pinMode(13,OUTPUT);
  digitalWrite(13,LOW);
  
  Serial.begin(115200);
  
  mode = TEST_MODE;
//  last_goal = millis();
//  last_push = millis();
  last_goal = 0;
  last_push = 0;
//  sensors_enabled = 1;
  
  Serial.println(SUB_READY);
}

void loop()
{
  int input = -1;
  if (Serial.available()>0)
  {
    input = Serial.parseInt();
    
    int consumed = 1;
    switch (input) {
      case COM_ECHO_TEST:
        Serial.println(SUB_ECHO_REPLY);
        break;
      case COM_SET_SLAVE_MODE:
        mode = SLAVE_MODE;
        Serial.println(SUB_SLAVE_MODE);
        break;
      case COM_SET_TEST_MODE:
        mode = TEST_MODE;
        Serial.println(SUB_TEST_MODE);
        break;
      case COM_RESET:
        setup();
        break;
      default:
        consumed = 0;
    }
    if (consumed) return;
  }

  if (mode == TEST_MODE) test_main(input);
  else slave_main(input);
  
  //delay(500);
  
}

void test_main(int input)
{
  int result = -1;
  if (input == COM_BLUE_NORMAL_TEST)
    result = digitalRead(BLUE1_PIN);
  else if (input == COM_BLUE_SUPER_TEST)
    result = digitalRead(BLUE2_PIN);
  else if (input == COM_RED_NORMAL_TEST)
    result = digitalRead(RED1_PIN);
  else if (input == COM_RED_SUPER_TEST)
    result = digitalRead(RED2_PIN);

  if (result != -1) {
    //Serial.println(result);
    if (result == 0) {
      Serial.println(SUB_TEST_OPEN);
    } else {
      Serial.println(SUB_TEST_CLOSE);
    }
  }
  
}

void slave_main(int input)
{
//  Serial.println("Begin slave main");
  if (millis() > last_goal + GOAL_DELAY)
//  if (sensors_enabled)
  {
     if (digitalRead(BLUE1_PIN))
     {
       Serial.println(SUB_PHOTO_BLUE_NORMAL);
       last_goal = millis();
//       while(digitalRead(BLUE1));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);
     }
     if (digitalRead(BLUE2_PIN))
     {
       Serial.println(SUB_PHOTO_BLUE_SUPER);
       last_goal = millis();
//       while(digitalRead(BLUE2));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);

     }
     if (digitalRead(RED1_PIN))
     {
       Serial.println(SUB_PHOTO_RED_NORMAL);
       last_goal = millis();
//       while(digitalRead(RED1));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);


     }
     if (digitalRead(RED2_PIN))
     {
       Serial.println(SUB_PHOTO_RED_SUPER);
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
       Serial.println(SUB_BUTTON_BLUE_GOAL);
       last_push = millis();
    }
    if (digitalRead(BLUE_UNDO_PIN))
    {
       Serial.println(SUB_BUTTON_BLUE_UNDO);
       last_push = millis();
    }
    if (digitalRead(RED_ADD_PIN))
    {
       Serial.println(SUB_BUTTON_RED_GOAL);
       last_push = millis();
    }
    if (digitalRead(RED_UNDO_PIN))
    {
       Serial.println(SUB_BUTTON_RED_UNDO);
       last_push = millis();
    }
  }
  
}

/*void enable_sensors()
{
  Serial.println("enable");
  sensors_enabled = 1;
}*/
