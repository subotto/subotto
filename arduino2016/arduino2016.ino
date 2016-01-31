/* Codice per l'Arduino dentro il SUBOTTO */

#include "SevSeg.h"
#include <SPI.h>
#include <EEPROM.h>
#include <Ethernet.h>
#include <utility/w5100.h>

#define DEBUG 0
#define TXID 1
#define RXID 2
#define DELAY_ETH_TIME 1000 //milliseconds
#define MAX_TRY 5

#define BRIGHTNESS 30
#define ERROR_TIMEOUT 3*1000

byte mac[] = { 90, 162, 218, 13, 78, 107};
byte server_ip[]={192, 168, 111, 243};
int porta=2204;
//ip del server da interrogare
EthernetClient client;
unsigned long int tempo=0;
int tentativi=0; //tentativi effettuati ad accedere al server

SevSeg blu; //inizializzo oggetto sevseg, ovvero i diplay a 7 segmenti
SevSeg rossi;

char C=0;
int z=10;
int counterrossi = 10000;
int counterblu = 10000; //rischio di overflow
int soglia=950; //varibile importantissima !!
long int last_contact = 0;
long int last_connection_retry = 0;
int loop_num = 0;
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
  byte data[4];
  if (!client.connected()) return;
  if (client.available() >= 4) {
    int i;
    for (i = 0; i < 4; i++) {
      data[i] = client.read();
    }
    counterrossi=data[0]*256+data[1];
    counterblu = data[2]*256+data[3];
    last_contact = millis();
  }
}

void Send(uint8_t data)
{
    client.write(data);
    
    #if DEBUG
    Serial.println("benone! invio riuscito");
    #endif
}



/*void LeggiPunteggio()
{
 counterrossi=EEPROM.read(0)*256+EEPROM.read(1);
 counterblu=EEPROM.read(2)*256+EEPROM.read(3);
}

void ScriviPunteggio(){
 EEPROM.write(0,counterrossi/256);
 EEPROM.write(1,counterrossi%256);
 EEPROM.write(2,counterblu/256);
 EEPROM.write(3,counterblu%256);
}*/

void SMS()
{
  //ScriviPunteggio();
  Send(wait);
}

/*void zero(){
  counterblu=0;
  counterrossi=0;
}*/

//prende i nuovi valori dei punteggi
  
void setup() {

  //DEBUG
   Serial.begin(9600);
  /*inizializzo i parametri relativi ai diplay a 7 segmenti */
  //start dell'ethernet
  if(Ethernet.begin(mac)==0){if(DEBUG)Serial.println("non connesso!");}
  /*
    In produzione, usare begin(mac, ip, dns, gateway, subnet); gli indirizzi sono tutti array di 4 byte.
  */
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
  blu.setBrightness(BRIGHTNESS);
  rossi.begin(COMMON_CATHODE, numDigits, digitPinsrossi , segmentPins);
  rossi.setBrightness(BRIGHTNESS);


  /*inizializzo i pin dei pulsanti*/
  pinMode(blupiu,INPUT);  //blu +
  pinMode(blumeno,INPUT);  //blu -
  pinMode(rossopiu,INPUT);  //rosso +
  pinMode(rossomeno,INPUT);  //rosso -
  pinMode(reset,INPUT);
  pinMode(A15, OUTPUT);//perchè si!
  //LeggiPunteggio();
  //Send(0);
  client.connect(server_ip, porta);
  receive_data();
  last_contact = millis();
  last_connection_retry = millis();
}



void loop() {  
  loop_num++;
  // Controllo della connessione
  Ethernet.maintain();
  if (((!client.connected()) || (millis() - last_contact >= ERROR_TIMEOUT)) && (millis() - last_connection_retry >= DELAY_ETH_TIME)) {
    Serial.println(client.connected());
    Serial.println(millis());
    Serial.println(last_contact);
    Serial.println(last_connection_retry);
    counterrossi = 10000;
    counterblu = 10000;
    int res;
    client.stop();
    res = client.connect(server_ip, porta);
    if (DEBUG) {
      Serial.print("connessione persa, riprovo; errore: ");
      Serial.println(res);
    }
    last_contact = millis();
    last_connection_retry = millis();
  }
  receive_data();
  
  //tutto il necessario per il debug
  /*if(DEBUG){
  Serial.print(analogRead(blup));Serial.print("  ");
  Serial.print(analogRead(blus));Serial.print("  ");
  Serial.print(analogRead(rossop));Serial.print("  ");
  Serial.print(analogRead(rossos));Serial.print("  ");
  Serial.print(digitalRead(blupiu));Serial.print("  ");
  Serial.print(digitalRead(blumeno));Serial.print("  ");
  Serial.print(digitalRead(rossopiu));Serial.print("  ");
  Serial.print(digitalRead(rossomeno));Serial.print("  ");
  Serial.println(digitalRead(reset));
  }*/
  //controllo tutti i possibili input
  if(analogRead(blup)>soglia) {
    if(!wait){
    wait=1;
    }
   if(DEBUG)C++;
  }
  else if(analogRead(blus)>soglia) {
    if(!wait){
      wait=2;
      }
      if(DEBUG)C++;
    }
  else if(analogRead(rossop)>soglia ) {
  if(!wait){
    wait=3;
    } //poco probabile
    if(DEBUG)C++;
  }
  else if(analogRead(rossos)>soglia ) {
    if(!wait){
      wait=4;
    }
    if(DEBUG)C++;
  } //idem     
  else if(digitalRead(blupiu)==HIGH) {    
    if(!wait){
      wait=5;
    }
    if(DEBUG)C++;
   }
  else if(digitalRead(blumeno)==HIGH ) {    if(!wait){
      wait=6;
    }
    if(DEBUG)C++;
   }
  else if(digitalRead(rossopiu)==HIGH) {    
    if(!wait){
      wait=7;
    }
    if(DEBUG)C++;
   }
  else if(digitalRead(rossomeno)==HIGH ) {    
    if(!wait){
      wait=8;
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
}
