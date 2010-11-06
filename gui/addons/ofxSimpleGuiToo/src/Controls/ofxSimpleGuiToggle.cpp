
#include "ofxSimpleGuiToggle.h"


ofxSimpleGuiToggle::ofxSimpleGuiToggle(string name, bool &value) : ofxSimpleGuiControl(name) {
	this->value	= &value;
	setMomentary(false);
	controlType = "Toggle";
	setup();
}

ofxSimpleGuiToggle& ofxSimpleGuiToggle::setMomentary(bool m) {
	momentary = m;
	return *this;
}


void ofxSimpleGuiToggle::setup() {
	setSize(config->gridSize.x - config->padding.x, config->toggleHeight);
}

void ofxSimpleGuiToggle::loadFromXML(ofxXmlSettings &XML) {
	setValue(XML.getValue(controlType + "_" + key + ":value", 0));
}

void ofxSimpleGuiToggle::saveToXML(ofxXmlSettings &XML) {
	XML.addTag(controlType + "_" + key);
	XML.pushTag(controlType + "_" + key);
	XML.addValue("name", name);
	XML.addValue("value", getValue());
	XML.popTag();
}


bool ofxSimpleGuiToggle::getValue() {
	return (*value);
}

void ofxSimpleGuiToggle::setValue(bool b) {
	(*value) = b;
}

void ofxSimpleGuiToggle::toggle() {
	(*value) = !(*value); 
}

void ofxSimpleGuiToggle::onPress(int x, int y, int button) {
	if(momentary) setValue(true);
	else toggle();
}

void ofxSimpleGuiToggle::onRelease(int x, int y, int button) {
	if(momentary) setValue(false);
}

void ofxSimpleGuiToggle::keyPressed( int key ) {
	if(key==keyboardShortcut) onPress(0, 0, 0);
}

void ofxSimpleGuiToggle::keyReleased( int key ) {
	if(key==keyboardShortcut) onRelease(0, 0, 0);
}

void ofxSimpleGuiToggle::onKeyEnter() {
	toggle();
}

void ofxSimpleGuiToggle::update() {
//	if(!enabled) return;
//	enabled = false;
}

void ofxSimpleGuiToggle::draw(float x, float y) {
//	enabled = true;
	setPos(x, y);
	
	glPushMatrix();
	glTranslatef(x, y, 0);
	
	ofEnableAlphaBlending();
	ofFill();
	setFullColor(*value);
	ofRect(0, 0, height, height);
	
	if((*value)) {
		setTextColor();
		ofLine(0, 0, height, height);
		ofLine(height, 0, 0, height);
	}
	
	setTextBGColor();
	ofRect(height, 0, width - height, height);
	
	setTextColor();
	ofDrawBitmapString(name, height + 15, 15);
	ofDisableAlphaBlending();
	
	glPopMatrix();
}

