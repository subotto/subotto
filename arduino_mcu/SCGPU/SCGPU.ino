//#include <SimpleTimer.h>

#define BLUE1 2
#define BLUE2 5
#define RED1 10
#define RED2 12

#define TEST_MODE 0
#define SLAVE_MODE 1

#define GOAL_DELAY 3000

int mode;
unsigned long last_goal;
//int sensors_enabled;

//SimpleTimer timer;

void setup()
{
  pinMode(BLUE1,INPUT_PULLUP);
  pinMode(BLUE2,INPUT_PULLUP);
  pinMode(RED1,INPUT_PULLUP);
  pinMode(RED2,INPUT_PULLUP);
  
  pinMode(13,OUTPUT);
  digitalWrite(13,LOW);
  
  Serial.begin(9600);
  
  mode = TEST_MODE;
  last_goal = millis();
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
    result = digitalRead(BLUE1);
  else if (input == 2)
    result = digitalRead(BLUE2);
  else if (input == 3)
    result = digitalRead(RED1);
  else if (input == 4)
    result = digitalRead(RED2);
  
  if (result != -1)
    Serial.println(result);
  
}




void slave_main(int input)
{
//  Serial.println("Begin slave main");
  if (millis() > last_goal + GOAL_DELAY)
//  if (sensors_enabled)
  {
     if (digitalRead(BLUE1))
     {
       Serial.println(1);
       last_goal = millis();
//       while(digitalRead(BLUE1));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);
     }
     if (digitalRead(BLUE2))
     {
       Serial.println(2);
       last_goal = millis();
//       while(digitalRead(BLUE2));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);

     }
     if (digitalRead(RED1))
     {
       Serial.println(3);
       last_goal = millis();
//       while(digitalRead(RED1));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);


     }
     if (digitalRead(RED2))
     {
       Serial.println(4);
       last_goal = millis();
//       while(digitalRead(RED2));
//        sensors_enabled = 0;
//        timer.setTimeout(GOAL_DELAY,enable_sensors);
     }
    
  }
//  else
//    Serial.println("not_enable");
  
}

/*void enable_sensors()
{
  Serial.println("enable");
  sensors_enabled = 1;
}*/
