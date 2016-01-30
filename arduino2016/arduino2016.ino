/* Codice per l'Arduino dentro il SUBOTTO */

#include "SevSeg.h"
#include <SPI.h>
#include <EEPROM.h>
#include <Ethernet.h>
#include <utility/w5100.h>

#define DEBUG 0
#define TXID 1
#define RXID 2
#define DELAY_ETH_TIME 10000 //milliseconds
#define MAX_TRY 5

byte mac[] = { 90, 162, 218, 13, 78, 107};
byte server_ip[]={172, 22, 0, 141};
int porta=2204;
//ip del server da interrogare
EthernetClient client;
unsigned long int tempo=0;
int tentativi=0; //tentativi effettuati ad accedere al server

SevSeg blu; //inizializzo oggetto sevseg, ovvero i diplay a 7 segmenti
SevSeg rossi;

char C=0;
int z=10;
int counterrossi = 0;
int counterblu = 0; //rischio di overflow
int soglia=950; //varibile importantissima !!
char wait = 0;

  //qui ci metto le varibili che conterranno i pin delle fotocellule
  byte blup=A1;
  byte blus=A3;
  byte rossop=A0;
  byte rossos=A2;
  
  
  //pulsanti
  byte blupiu=5;
  byte blumeno=4;
  byte rossopiu=7;
  byte rossomeno=6; //molto probabile
  byte reset=8;
  



/*int GetServerMessage(uint8_t*messaggio, int bufflen)
{
    int j=0;
    int risposta=1;
    int tentativi=0;
    while(risposta && j <bufflen){
    while(!client.available() && tentativi<10)
    {
      tentativi++;
      #if DEBUG
      Serial.println("Ho provato "+String(tentativi)+" volte");
      #endif
      delay(200);
    }
    if(tentativi==10){risposta=0; 
    #if DEBUG
    Serial.println("Non ho ricevuto risposta dal server");
    return 0;
    #endif
    }
    uint8_t c =(uint8_t)client.read();
    messaggio[j]=c;
    j++;
    #if DEBUG
    Serial.println("risposta ="+String(c));
    #endif
    }
    client.stop();
    return 1;
}*/

void receive_data() {
  unit8_t data[4];
  if (client.available() >= 4) {
    int i;
    for (i = 0; i < 4; i++) {
      data[i] = client.read();
    }
    counterrossi=data[0]*256+data[1];
    counterblu = data[2]*256+data[3];    
  }
}

void Send(uint8_t data)
{
  if(tentativi>MAX_TRY)return;
  Serial.println("Provo a collegarmi");
  if (client.connect(server_ip, porta)) {
    tentativi=0;
    #if DEBUG
    Serial.println("connesso, ora mando al server "+String(data));
    #endif
    
    client.write(data);
    
    #if DEBUG
    Serial.println("benone! connessione riuscita, aspettiamo risposta");
    #endif
    
    uint8_t messaggio[4]={0};
    GetServerMessage(messaggio, 4);
    Serial.println("Cavolo si che ci passi");
  }
  else
  {
    tentativi++;
  #if DEBUG
  Serial.println("malaccio!");
  #endif
  }
}



void LeggiPunteggio()
{
 counterrossi=EEPROM.read(0)*256+EEPROM.read(1);
 counterblu=EEPROM.read(2)*256+EEPROM.read(3);
}

void ScriviPunteggio(){
 EEPROM.write(0,counterrossi/256);
 EEPROM.write(1,counterrossi%256);
 EEPROM.write(2,counterblu/256);
 EEPROM.write(3,counterblu%256);
}

void SMS()
{
  ScriviPunteggio();
  Send(wait);
}

void zero(){
  counterblu=0;
  counterrossi=0;
}

//prende i nuovi valori dei punteggi
  
void setup() {

  //DEBUG
   Serial.begin(9600);
  /*inizializzo i parametri relativi ai diplay a 7 segmenti */
  //start dell'ethernet
  if(Ethernet.begin(mac)==0){if(DEBUG)Serial.println("non connesso!");}
  #if DEBUG
  else Serial.println("connesso");
  #endif
  W5100.setRetransmissionTime(300);
  W5100.setRetransmissionCount(1);
  delay(1000);


  
  byte numDigits = 4; // numero di cifre da con trollare per diplay  
  byte digitPinsblu[] = {30, 32, 34, 36}; // pin di Arduino che controllano le cifre del diplay dei blu
  byte digitPinsrossi[] = {22 , 24, 26, 28}; // come sopra per i rossi
  byte segmentPins[] = {38, 40, 42, 44, 46, 48, A15, 25};  // pin di Arduino che pilatano i segmenti
  
  blu.begin(COMMON_CATHODE, numDigits, digitPinsblu, segmentPins);
  blu.setBrightness(10);
  rossi.begin(COMMON_CATHODE, numDigits, digitPinsrossi , segmentPins);
  rossi.setBrightness(10);


  /*inizializzo i pin dei pulsanti*/
  pinMode(blupiu,INPUT);  //blu +
  pinMode(blumeno,INPUT);  //blu -
  pinMode(rossopiu,INPUT);  //rosso +
  pinMode(rossomeno,INPUT);  //rosso -
  pinMode(reset,INPUT);
  pinMode(A15, OUTPUT);//perchè si!
  LeggiPunteggio();
  Send(0);
}



void loop() {  
  //tutto il necessario per il debug
  if(DEBUG){
  Serial.print(analogRead(blup));Serial.print("  ");
  Serial.print(analogRead(blus));Serial.print("  ");
  Serial.print(analogRead(rossop));Serial.print("  ");
  Serial.print(analogRead(rossos));Serial.print("  ");
  Serial.print(digitalRead(blupiu));Serial.print("  ");
  Serial.print(digitalRead(blumeno));Serial.print("  ");
  Serial.print(digitalRead(rossopiu));Serial.print("  ");
  Serial.print(digitalRead(rossomeno));Serial.print("  ");
  Serial.println(digitalRead(reset));
  }
  //controllo tutti i possibili input
  if(analogRead(blup)>soglia) {
    if(!wait){
    counterblu++; wait=1;
    }
   if(DEBUG)C++;
  }
  else if(analogRead(blus)>soglia) {
    if(!wait){
      counterblu++; wait=2;
      }
      if(DEBUG)C++;
    }
  else if(analogRead(rossop)>soglia ) {
  if(!wait){
    counterrossi++; wait=3;
    } //poco probabile
    if(DEBUG)C++;
  }
  else if(analogRead(rossos)>soglia ) {
    if(!wait){
      counterrossi++; wait=4;
    }
    if(DEBUG)C++;
  } //idem     
  else if(digitalRead(blupiu)==HIGH) {    
    if(!wait){
      counterblu++; wait=5;
    }
    if(DEBUG)C++;
   }
  else if(digitalRead(blumeno)==HIGH ) {    if(!wait){
      counterblu--; wait=6;
    }
    if(DEBUG)C++;
   }
  else if(digitalRead(rossopiu)==HIGH) {    
    if(!wait){
      counterrossi++; wait=7;
    }
    if(DEBUG)C++;
   }
  else if(digitalRead(rossomeno)==HIGH ) {    
    if(!wait){
      counterrossi--; wait=8;
    }
    if(DEBUG)C++;
   }
  else if(wait){
    //si, lo facciamo quando finiamo il pooling
    SMS();
    if(DEBUG){
      if(z<4000){
        EEPROM.write(z,wait);
        Serial.println("scrivo :"+String((int)wait)+" in "+String((int)C));
        EEPROM.write(z+1,C);
        z=z+2;
        C=0;      }
    }
    wait=0;
  }
  
  blu.setNumber(counterblu,0);
  blu.refreshDisplay();
  rossi.setNumber(counterrossi,0);
  rossi.refreshDisplay();
  
  //vado a vedere se qualcosa è cambiata comunque
  int t=millis();
  if(t-tempo>DELAY_ETH_TIME)
  {
    Send(0);
    tempo=t;
  }
}
