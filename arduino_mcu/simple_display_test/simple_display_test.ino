#include "LedControl.h"

#define SPI_CLK 12		// Clock
#define SPI_MOSI 11		// Master Out Slave In 
#define SPI_MISO 100	// Master In Slave Out - per i led non ci serve questa porta

#define SPI_DISPLAY_LOAD 13	 // Load per il display

LedControl lc=LedControl(SPI_MOSI, SPI_CLK,SPI_DISPLAY_LOAD,1);

void writeInteger(int number, int display_number)
//	Scrivi l'intero numero su display (0 o 1)
//	Gli zeri iniziali vengono buttati via
//	Le cifre 0 (per display 0) e 4 (per display 1) sono le più significative
{
	display_number *= 4;
	for ( int   i = 3 ; i > 0 ; --i)
	{
		lc.setDigit(0,i+display_number,number%10, false);
		number /= 10; 
		if (number == 0 ) return ;
	}
}

void refreshDisplay(int input)
{
  input -= 10000;
  writeInteger ( input % 10000 , 1-input/10000);
}

void setup()
{
 // pinMode(13,OUTPUT);		// led per debug
 // digitalWrite(13,LOW);
  
  Serial.begin(9600);
  Serial.println("I'm ready");
}

void loop() {
  while (Serial.available() > 0) {
    int input = Serial.parseInt();
    
    if (Serial.read() != '\n')
      continue;
      
    Serial.println(input);
    refreshDisplay(input);
  }
}
