
#include "ofxSimpleGuiSlider2d.h"


ofxSimpleGuiSlider2d::ofxSimpleGuiSlider2d(string name, ofPoint& value, float xmin, float xmax, float ymin, float ymax) : ofxSimpleGuiControl(name) {
	min.set(xmin, ymin);
	max.set(xmax, ymax);
	this->value = &value;
	controlType = "Slider2D";
	setup();
}

void ofxSimpleGuiSlider2d::setup() {
	setSize(config->slider2DSize.x, config->slider2DSize.y + config->slider2DTextHeight);
	point.x = ofMap((*value).x, min.x, max.x, x, x+width);
	point.y = ofMap((*value).y, min.y, max.y, y, y+height-config->slider2DTextHeight);
}

void ofxSimpleGuiSlider2d::loadFromXML(ofxXmlSettings &XML) {
	value->set(XML.getValue(controlType + "_" + key + ":valueX", 0.0f), XML.getValue(controlType + "_" + key + ":valueY", 0.0f));
}


void ofxSimpleGuiSlider2d::saveToXML(ofxXmlSettings &XML) {
	XML.addTag(controlType + "_" + key);
	XML.pushTag(controlType + "_" + key);
	XML.addValue("name", name);
	XML.addValue("valueX", value->x);
	XML.addValue("valueY", value->y);
	XML.popTag();
}


void ofxSimpleGuiSlider2d::setValue(float x, float y) {
	(*value).x = x;
	(*value).y = y;
}

void ofxSimpleGuiSlider2d::setMin(float x, float y) {
	min.x = x;
	min.y = y;
}

void ofxSimpleGuiSlider2d::setMax(float x, float y) {
	max.x = x;
	max.y = y;
}

void ofxSimpleGuiSlider2d::onPress(int x, int y, int button) {
	lock = true;
	point.set(x, y);
}

void ofxSimpleGuiSlider2d::onDragOver(int x, int y, int button) {
	if(lock) {
		point.set(x, y);
	}
}

void ofxSimpleGuiSlider2d::onDragOutside(int x, int y, int button) {
	if(lock) {
		point.set(x, y);
	}
}

void ofxSimpleGuiSlider2d::onRelease() {
	lock = false;
}

void ofxSimpleGuiSlider2d::update() {
	if(point.x > x + width)				point.x = x + width;
	else if(point.x < x)				point.x = x;
	
	if(point.y > y+height - config->slider2DTextHeight)			point.y = y + height - config->slider2DTextHeight;
	else if(point.y < y)				point.y = y;
	
	if(lock){
		(*value).x = ofMap(point.x, x, x+width, min.x, max.x);
		(*value).y = ofMap(point.y, y, y+height-config->slider2DTextHeight, min.y, max.y);
	}
}

void ofxSimpleGuiSlider2d::draw(float x, float y) {
	setPos(x, y);
	ofPoint	pointv;
	pointv.x = ofMap((*value).x, min.x, max.x, x, x+width);
	pointv.y = ofMap((*value).y, min.y, max.y, y, y+height-config->slider2DTextHeight);
	
	ofEnableAlphaBlending();
	glPushMatrix();
	glTranslatef(x, y, 0);
	
	ofFill();
	setFullColor();
	ofRect(0, 0, width, height - config->slider2DTextHeight);
	
	ofFill();
	setTextBGColor();
	ofRect(0, height-config->slider2DTextHeight, width, config->slider2DTextHeight);
	
	setTextColor();
	ofDrawBitmapString(name+"\nx:"+ofToString(value->x, 2)+"\ny:"+ofToString(value->y, 2), 3, height+15-config->slider2DTextHeight);
	
	setTextColor();
	ofCircle(pointv.x-x, pointv.y-y, 2);
	
	setTextColor();
	ofLine(pointv.x-x, 0, pointv.x-x, height-config->slider2DTextHeight);
	ofLine(0, pointv.y-y,width, pointv.y-y);
	
	glPopMatrix();
	ofDisableAlphaBlending();
	
}