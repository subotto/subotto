// Porte di I/O su Arduino

#define BLUE_NORMAL_PIN 3
#define BLUE_SUPER_PIN 5
#define RED_NORMAL_PIN 2
#define RED_SUPER_PIN 4

#define GOAL_DELAY 1000

int last_goal=0;

void setup()
{
  pinMode(BLUE_NORMAL_PIN,INPUT);
  pinMode(BLUE_SUPER_PIN,INPUT);
  pinMode(RED_NORMAL_PIN,INPUT);
  pinMode(RED_SUPER_PIN,INPUT);
  
  pinMode(13,OUTPUT);		// led per debug
  digitalWrite(13,LOW);
  
  Serial.begin(9600);
  Serial.println("I'm ready");
}

void loop()
{
  // Scansione delle fotocellule
  if (millis() > last_goal + GOAL_DELAY)
  {
     if (digitalRead(BLUE_NORMAL_PIN))
     {
       Serial.println("blue normal");
       last_goal = millis();
     }
     if (digitalRead(BLUE_SUPER_PIN))
     {
       Serial.println("blue super");
       last_goal = millis();
     }
     if (digitalRead(RED_NORMAL_PIN))
     {
       Serial.println("red normal");
       last_goal = millis();
     }
     if (digitalRead(RED_SUPER_PIN))
     {
       Serial.println("red super");
       last_goal = millis();
     }
  }
}
