#define SOUND_SENSOR_PIN D8  // Digital pin for sound sensor

float phase = 0;  // Phase for sine wave
const float phaseIncrement = 0.01;  // Reduce increment step for smoother sine wave
int amplitude = 512;  // Amplitude of sine wave (half of max analog value 1023)

void setup() {
  Serial.begin(115200);  // Start serial communication at 115200 baud rate
  pinMode(SOUND_SENSOR_PIN, INPUT);
}

void loop() {
  int sensorValue = digitalRead(SOUND_SENSOR_PIN);  // Read digital sound sensor value (HIGH/LOW)
  
  if (sensorValue == HIGH) {
    // Generate a sine wave
    float sineWaveValue = amplitude * (sin(phase));  // Calculate sine wave value
    int plotValue = (int)(sineWaveValue + amplitude);  // Shift to positive range for plotting

    // Print the sine wave value to Serial Plotter
    Serial.println(plotValue);

    // Increment phase to progress the sine wave
    phase += phaseIncrement;
    if (phase > TWO_PI) {
      phase -= TWO_PI;  // Keep phase within 0 to 2π
    }
  } else {
    // When no sound is detected, reset the phase and print zero to keep the graph stable
    phase = 0;
    Serial.println(0);  // Output zero when there's no sound detected
  }

  delay(100);  // Increase delay to 100ms to slow down the plot
}