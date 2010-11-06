#pragma once

#include "ofxSimpleGuiControl.h"

#include "ofxSimpleGuiSliderBase.h"


class ofxSimpleGuiSliderInt : public ofxSimpleGuiSliderBase<int> {
	
public:
	ofxSimpleGuiSliderInt(string name, int &value, int min, int max) : ofxSimpleGuiSliderBase<int>(name, value, min, max) {
		controlType = "SliderInt";
		setIncrement(1);
	}

};
