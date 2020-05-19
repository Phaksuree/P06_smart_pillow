#include <ArduinoJson.h>
#include <WiFi.h>
#include <Wire.h>
#include <jsmn.h>
#include <HTTPClient.h>
#include <Adafruit_ADS1015.h>

Adafruit_ADS1115 ads_1(0x48);
Adafruit_ADS1115 ads_2(0x49);
Adafruit_ADS1115 ads_3(0x4A);

#define WIFI_SSID "Babynanny"
#define WIFI_PASSWORD "bebenani"

char jsonOutput[128];
int Round = 0;
int16_t cal[9];
int16_t adc[9];
  
void setup() {
  Serial.begin(115200);
  ads_1.begin();
  ads_2.begin();
  ads_3.begin();

  WiFi.mode(WIFI_STA);
  // connect to wifi.
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("connecting");

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();
  Serial.print("connected: ");
  Serial.println(WiFi.localIP());

}

void loop() {
  delay(1000);
  adc[0] = (ads_3.readADC_SingleEnded(0))/4;
  adc[1] = (ads_1.readADC_SingleEnded(1))/4;
  adc[2] = (ads_1.readADC_SingleEnded(2))/4;
  adc[3] = (ads_1.readADC_SingleEnded(3))/4;
  adc[4] = (ads_2.readADC_SingleEnded(0))/4;
  adc[5] = (ads_2.readADC_SingleEnded(1))/4;
  adc[6] = (ads_2.readADC_SingleEnded(2))/4;
  adc[7] = (ads_2.readADC_SingleEnded(3))/4;
  adc[8] = (ads_3.readADC_SingleEnded(2))/4;
  delay(1000);
  if (Round < 4){
    for (int i = 0; i < 9; i = i + 1) {
      cal[i] += adc[i];
      }
   }
  if (Round == 4){
    for (int i = 0; i < 9; i = i + 1) {
      cal[i] += adc[i];
     }
    for (int i = 0; i < 9; i = i + 1) {
      cal[i] = cal[i]/3;
      Serial.println(cal[i]);
    }
  }
  if (Round >= 5){
    for (int i = 0; i < 9; i = i + 1) {    
      adc[i] -= cal[i];
      if (adc[i] < 800){
        adc[i] = 0;
      } 
    }
  }
    Serial.println("===========================");
    Serial.print(adc[0]); Serial.print("      ");
    Serial.print(adc[1]); Serial.print("      ");
    Serial.println(adc[2]);
    Serial.print(adc[3]); Serial.print("      ");
    Serial.print(adc[4]); Serial.print("      ");
    Serial.println(adc[5]);
    Serial.print(adc[6]); Serial.print("      ");
    Serial.print(adc[7]); Serial.print("      ");
    Serial.println(adc[8]);
 
  if (Round >= 10 ){
    if(WiFi.status()== WL_CONNECTED){   //Check WiFi connection status
      HTTPClient http; 
      //http.begin("http://172.20.10.3:8080/predict");//Specify destination for HTTP request
      http.begin("http://34.87.85.156:8080/predict");
      http.addHeader("Content-Type", "application/json");  //Specify content-type header

      StaticJsonBuffer<300> JSONbuffer;
      JsonObject& JSONencoder = JSONbuffer.createObject();
      JsonArray& values = JSONencoder.createNestedArray("data"); //JSON array
      values.add(adc[0]); //Add value to array
      values.add(adc[1]); //Add value to array
      values.add(adc[2]); //Add value to array
      values.add(adc[3]); //Add value to array
      values.add(adc[4]); //Add value to array
      values.add(adc[5]); //Add value to array
      values.add(adc[6]); //Add value to array
      values.add(adc[7]); //Add value to array
      values.add(adc[8]); //Add value to array
      char JSONmessageBuffer[300];
      JSONencoder.prettyPrintTo(JSONmessageBuffer, sizeof(JSONmessageBuffer));
      Serial.println(JSONmessageBuffer);

//      serializeJson(JSONmessageBuffer);
//      Serial.println(jsonOutput);
      int httpResponseCode = http.POST(JSONmessageBuffer); //Send the actual POST request
//      int httpResponseCode = http.GET();
  
      if(httpResponseCode>0){
        String response = http.getString();                       //Get the response to the request
        Serial.println(httpResponseCode);   //Print return code
        Serial.println(response);           //Print request answer
      }else{
        Serial.print("Error on sending POST: ");
        Serial.println(httpResponseCode);
      }
      http.end();  //Free resources
      }else{
      Serial.println("Error in WiFi connection");   
      }
      delay(25000);
    }
    
  delay(2000);
  Round++;
  Serial.println(Round);
}
