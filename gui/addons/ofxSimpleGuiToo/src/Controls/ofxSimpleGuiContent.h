#pragma once

#include "ofxSimpleGuiControl.h"


class ofxSimpleGuiContent  : public ofxSimpleGuiControl {
public:
	float			fixwidth;
	float			fixheight;
	ofBaseDraws		*content;

	ofxSimpleGuiContent(string name, ofBaseDraws& content, float fixwidth=250.0);
	void setup();
	void draw(float x, float y);
};
