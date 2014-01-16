// Porte di I/O su Arduino

#define BLUE_ADD_PIN 8
#define BLUE_UNDO_PIN 10
#define RED_ADD_PIN 11
#define RED_UNDO_PIN 9

void setup()
{
  pinMode(BLUE_ADD_PIN,INPUT_PULLUP);
  pinMode(BLUE_UNDO_PIN,INPUT_PULLUP);
  pinMode(RED_ADD_PIN,INPUT_PULLUP);
  pinMode(RED_UNDO_PIN,INPUT_PULLUP);
  
  pinMode(13,OUTPUT);		// led per debug
  digitalWrite(13,LOW);
  
  Serial.begin(9600);
  Serial.println("I'm ready");
}

void loop()
{
    if (!digitalRead(BLUE_ADD_PIN))
    {
       Serial.println("Blue goal");
    }
    if (!digitalRead(BLUE_UNDO_PIN))
    {
       Serial.println("Blue undo");
    }
    if (!digitalRead(RED_ADD_PIN))
    {
       Serial.println("Red goal");
    }
    if (!digitalRead(RED_UNDO_PIN))
    {
       Serial.println("Red undo");
    }
}
