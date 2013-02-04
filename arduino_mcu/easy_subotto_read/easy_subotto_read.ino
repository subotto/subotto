
#define BLUE_NORMAL_PIN 10
#define BLUE_SUPER_PIN 8
#define RED_NORMAL_PIN 5
#define RED_SUPER_PIN 3

void setup()
{
  pinMode(BLUE_NORMAL_PIN,INPUT);
  pinMode(BLUE_SUPER_PIN,INPUT);
  pinMode(RED_NORMAL_PIN,INPUT);
  pinMode(RED_SUPER_PIN,INPUT);
  Serial.begin(9600);
}

void loop()
{
  if (digitalRead(BLUE_NORMAL_PIN))
  {
    Serial.println("Blu normale");
  }
  if (digitalRead(BLUE_SUPER_PIN))
  {
    Serial.println("Blu super");
  }
  if (digitalRead(RED_NORMAL_PIN))
  {
    Serial.println("Rosso normale");
  }
  if (digitalRead(RED_SUPER_PIN))
  {
    Serial.println("Rosso super");
  }
  //delay(50);
}
  
