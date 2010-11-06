#pragma once

#include "ofxSimpleGuiControl.h"

class ofxSimpleGuiTitle : public ofxSimpleGuiControl {
	
public:
	
	bool*			value;
	bool			beToggle;
	bool			beenPressed;

	ofxSimpleGuiTitle(string name, float height);
	void setup();
	void loadFromXML(ofxXmlSettings &XML);
	void saveToXML(ofxXmlSettings &XML);
	bool getValue();
	void setValue(bool b);
	void toggle();
	void setToggleMode(bool b);
	void onPress(int x, int y, int button);
	void onRelease(int x, int y, int button);
	void draw(float x, float y);
};
