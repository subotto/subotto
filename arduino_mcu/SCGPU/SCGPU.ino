#include "opcodes.h"
#include "LedControl.h"

// Porte di I/O su Arduino

#define BLUE_NORMAL_PIN 10
#define BLUE_SUPER_PIN 8
#define RED_NORMAL_PIN 5
#define RED_SUPER_PIN 3

#define BLUE_ADD_PIN 12
#define BLUE_UNDO_PIN 12
#define RED_ADD_PIN 12
#define RED_UNDO_PIN 12

// Interfacce seriali 

#define SPI_CLK 11		// Clock
#define SPI_MOSI 12		// Master Out Slave In 
#define SPI_MISO 100	// Master In Slave Out - per i led non ci serve questa porta

#define SPI_DISPLAY_LOAD 10	 // Load per il display


// Settaggi

#define GOAL_DELAY 3000
#define PUSH_DELAY 5000
#define DELAY 10


// Costanti del programma

#define TEST_MODE 0
#define SLAVE_MODE 1

int mode;	// l'attuale modalità di lavoro
unsigned long last_goal;	// il millis dell'ultimo goal
unsigned long last_push;	// il millis dell'ultima pressione di pulsante

LedControl lc=LedControl(SPI_MOSI, SPI_CLK,SPI_DISPLAY_LOAD,1);

void scriviIntero(int numero, int display)
/*
	Scrivi l'intero numero su display (0 o 1)
	Gli zeri iniziali vengono buttati via
	Le cifre 0 (per display 0) e 4 (per display 1) sono le più significative
*/
{
	display *= 4;
	for ( i = 3 ; i > 0 ; --i)
	{
		lc.setDigit(0,i+display,numero%10, false);
		numero /= 10; 
		if (numero == 0 ) return ;
	}
}

void setup()
{
  pinMode(BLUE_NORMAL_PIN,INPUT);
  pinMode(BLUE_SUPER_PIN,INPUT);
  pinMode(RED_NORMAL_PIN,INPUT);
  pinMode(RED_SUPER_PIN,INPUT);
  
  pinMode(BLUE_ADD_PIN,INPUT_PULLUP);
  pinMode(BLUE_UNDO_PIN,INPUT_PULLUP);
  pinMode(RED_ADD_PIN,INPUT_PULLUP);
  pinMode(RED_UNDO_PIN,INPUT_PULLUP);
  
  pinMode(13,OUTPUT);		// led per debug
  digitalWrite(13,LOW);
  
  Serial.begin(115200);
  
  mode = TEST_MODE;
//  last_goal = millis();
//  last_push = millis();
  last_goal = 0;
  last_push = 0;
  
  // Inizializzazione del display
  /*
   The MAX72XX is in power-saving mode on startup,
   we have to do a wakeup call
   */
  lc.shutdown(0,false);
  /* Set the brightness to a medium values */
  lc.setIntensity(0,8);
  /* and clear the display */
  lc.clearDisplay(0);
  scriviIntero(0,0);
  scriviIntero(0,1);
  
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
  
  delay(DELAY);
  
}

void test_main(int input)
{
  int result = -1;
  
  // Se mi è stato chiesto di leggere un sensore rispondo
  if (input == COM_BLUE_NORMAL_TEST)
    result = digitalRead(BLUE_NORMAL_PIN);
  else if (input == COM_BLUE_SUPER_TEST)
    result = digitalRead(BLUE_SUPER_PIN);
  else if (input == COM_RED_NORMAL_TEST)
    result = digitalRead(RED_NORMAL_PIN);
  else if (input == COM_RED_SUPER_TEST)
    result = digitalRead(RED_SUPER_PIN);

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
	
  // Scansione delle fotocellule
  if (millis() > last_goal + GOAL_DELAY)
  {
     if (digitalRead(BLUE_NORMAL_PIN))
     {
       Serial.println(SUB_PHOTO_BLUE_NORMAL);
       last_goal = millis();
     }
     if (digitalRead(BLUE_SUPER_PIN))
     {
       Serial.println(SUB_PHOTO_BLUE_SUPER);
       last_goal = millis();
     }
     if (digitalRead(RED_NORMAL_PIN))
     {
       Serial.println(SUB_PHOTO_RED_NORMAL);
       last_goal = millis();
     }
     if (digitalRead(RED_SUPER_PIN))
     {
       Serial.println(SUB_PHOTO_RED_SUPER);
       last_goal = millis();
     }
  }


  // Scansione dei pulsanti
//  if (millis() > last_push + PUSH_DELAY)
  if (0 == 1)		// non sono ancora collegati
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

