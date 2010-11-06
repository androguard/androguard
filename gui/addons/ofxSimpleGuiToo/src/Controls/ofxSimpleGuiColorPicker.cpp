/*
 *  ofxSimpleGuiColorPicker.cpp
 *  OpenCL Particles 3. single segment trails
 *
 *  Created by Mehmet Akten on 01/11/2009.
 *  Copyright 2009 __MyCompanyName__. All rights reserved.
 *
 */

#include "ofxSimpleGuiColorPicker.h"

ofxSimpleGuiColorPicker::ofxSimpleGuiColorPicker(string name, float* value, float max) : ofxSimpleGuiControl(name) {
	this->value = value;
	this->min	= 0;
	this->max	= max;
	
	controlType = "ColorPicker";
	setup();
}

void ofxSimpleGuiColorPicker::setup() {
	setSize(config->gridSize.x - config->padding.x, config->sliderHeight * 8 + config->sliderTextHeight);
	for(int i=0; i<4; i++) {
		pct[i] = ofMap(getValue(i), 0, max, 0.0, width);
		barwidth[i] = pct[i];
	}
}

void ofxSimpleGuiColorPicker::loadFromXML(ofxXmlSettings &XML) {
	for(int i=0; i<4; i++) {
		setValue(XML.getValue(controlType + "_" + key + ":values_" + ofToString(i), 0.0f), i);
	}
}

void ofxSimpleGuiColorPicker::saveToXML(ofxXmlSettings &XML) {
	XML.addTag(controlType + "_" + key);
	XML.pushTag(controlType + "_" + key);
	XML.addValue("name", name);
	for(int i=0; i<4; i++) {
		XML.addValue("values_" + ofToString(i), getValue(i));
	}
	XML.popTag();
}



float ofxSimpleGuiColorPicker::getValue(int i) {
	return (value)[i];
}


void ofxSimpleGuiColorPicker::setValue(float f, int i) {
	if(f < min) f = min;
	else if(f > max) f = max;
	(value)[i] = f;
}


void ofxSimpleGuiColorPicker::updateSlider() {
	if(!enabled) return;
	
	int i= (getMouseY() - y) / config->sliderHeight/2;
	if(i<0 || i>=4) return;
	
	if(pct[i] > width) {
		pct[i] = width;
	}
	else {
		pct[i] = getMouseX() - x;
		setValue(ofMap(pct[i], 0.0, (float)width, 0, max), i);
	}
}

void ofxSimpleGuiColorPicker::onPress(int x, int y, int button) {
	updateSlider();
}

void ofxSimpleGuiColorPicker::onDragOver(int x, int y, int button) {
	updateSlider();
}

void ofxSimpleGuiColorPicker::onDragOutside(int x, int y, int button) {
	updateSlider();
}



//--------------------------------------------------------------------- update
void ofxSimpleGuiColorPicker::update() {
	if(!enabled) return;
	
	if(lock) {
		updateSlider();
	}
	
//	enabled = false;
}

//--------------------------------------------------------------------- draw
void ofxSimpleGuiColorPicker::draw(float x, float y) {
	
//	enabled = true;
	
	//update postion of gui object
	setPos(x, y);
	glPushMatrix();
	glTranslatef(x, y, 0);
	
	int startY = 0;
	for(int i=0; i<4; i++) {
		
		barwidth[i] = ofMap(getValue(i), 0, max, 0.0, (float)width);
		if(barwidth[i] > width)	barwidth[i] = width;
		else if(barwidth[i] < 0) barwidth[i] = 0;
		
		ofEnableAlphaBlending();
		ofFill();
		setEmptyColor();
		ofRect(0, startY, width, config->sliderHeight*1.8);
		
	
		switch(i) {
			case 0:glColor3f(getValue(i), 0, 0); break;
			case 1:glColor3f(0, getValue(i), 0); break;
			case 2:glColor3f(0, 0, getValue(i)); break;
			case 3:glColor3f(getValue(i), getValue(i), getValue(i)); break;
		}
		
		ofRect(0, startY, barwidth[i], config->sliderHeight * 1.8);
		
		int iover = (getMouseY() - y) / config->sliderHeight/2;
		bool isOver = iover == i;
		if(isOver) {
			glColor3f(1, 1, 1);
		} else {
			glColor3f(0.5, 0.5, 0.5);
		}
		
		ofDrawBitmapString(ofToString(getValue(i), 4), 3, startY + 14);
		
		startY += config->sliderHeight * 2;
	}
	
	ofFill();
	
	setTextBGColor();
	ofRect(0, startY, width, config->sliderTextHeight);

	glColor3f(getValue(0), getValue(1), getValue(2));
//	ofRect(0, startY+config->sliderTextHeight, width, config->sliderTextHeight * 1.5);
	ofRect(150, startY + 3, width - 150 -3, config->sliderTextHeight - 8);
	
	setTextColor();
	string s = name;
	ofDrawBitmapString(s, 3, startY + 14);
	ofDisableAlphaBlending();
	glPopMatrix();
}
