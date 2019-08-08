void FillLEDsFromPaletteColors( uint8_t colorIndex)
{
    uint8_t brightness = 255;
    
    for( int i = 0; i < NUM_LEDS; i++) {
        leds[i] = ColorFromPalette( currentPalette, colorIndex, brightness, currentBlending);
        colorIndex += 3;
    }
    leds[6] = CRGB::Black;
    leds[7] = CRGB::Black;
    leds[8] = CRGB::Black;
    leds[9] = CRGB::Black;
    leds[10] = CRGB::Black;
    leds[11] = CRGB::Black;
}

void SetupBlackAndWhiteStripedPalette()
{
    fill_solid( currentPalette, 16, CRGB::White);
}
