#pragma once

#include "ofxSimpleGuiControl.h"

#include "ofxSimpleGuiSliderBase.h"


class ofxSimpleGuiSliderFloat : public ofxSimpleGuiSliderBase<float> {
	
public:
	ofxSimpleGuiSliderFloat(string name, float &value, float min, float max) : ofxSimpleGuiSliderBase<float>(name, value, min, max) {
		controlType = "SliderFloat";
	}
};
