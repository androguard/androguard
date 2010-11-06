#pragma once

#include "ofxSimpleGuiControl.h"


class ofxSimpleGuiSlider2d : public ofxSimpleGuiControl {
public:
	ofPoint		*value;
	ofPoint		point, min, max;

	ofxSimpleGuiSlider2d(string name, ofPoint& value, float xmin, float xmax, float ymin, float ymax);
	void setup();
	void loadFromXML(ofxXmlSettings &XML);
	void saveToXML(ofxXmlSettings &XML);
	void setValue(float x, float y);
	void setMin(float x, float y);
	void setMax(float x, float y);
	void onPress(int x, int y, int button);
	void onDragOver(int x, int y, int button);
	void onDragOutside(int x, int y, int button);
	void onRelease();
	void update();
	void draw(float x, float y);
};
