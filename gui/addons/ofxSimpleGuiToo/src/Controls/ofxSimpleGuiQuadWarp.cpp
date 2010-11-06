
#include "ofxSimpleGuiQuadWarp.h"

#define MOUSE_DISTANCE		10.0f

//---------------------------------------------------------------------
ofxSimpleGuiQuadWarp::ofxSimpleGuiQuadWarp(string name, ofBaseDraws &baseDraw, ofPoint *pts) : ofxSimpleGuiControl(name) {
	this->baseDraw = &baseDraw;
	
	setPos(0, 0);
	setSize(baseDraw.getWidth(), baseDraw.getHeight());
	
	curPoint	= NULL;
	this->pts = pts;
	
	for(int i=0; i<4; i++) pts[i].z = i;		// z axis stores the index
	
	controlType = "QuadWarp";
	setup();
}

void ofxSimpleGuiQuadWarp::setup() {
	
}


void ofxSimpleGuiQuadWarp::loadFromXML(ofxXmlSettings &XML) {
	for(int i=0; i<4; i++) {
		pts[i].x = XML.getValue(controlType + "_" + key + ":values_" + ofToString(i) + "_x", 0.0f);
		pts[i].y = XML.getValue(controlType + "_" + key + ":values_" + ofToString(i) + "_y", 0.0f);
	}
}

void ofxSimpleGuiQuadWarp::saveToXML(ofxXmlSettings &XML) {
	XML.addTag(controlType + "_" + key);
	XML.pushTag(controlType + "_" + key);
	XML.addValue("name", name);
	for(int i=0; i<4; i++) {
		XML.addValue("values_" + ofToString(i) + "_x", pts[i].x);
		XML.addValue("values_" + ofToString(i) + "_y", pts[i].y);
	}
	XML.popTag();
}



//---------------------------------------------------------------------
void ofxSimpleGuiQuadWarp::onPress(int x, int y, int button) {
	curPoint = NULL;
	for(int i=0; i<4; i++) {
		if(ofDistSquared(x - this->x, y - this->y, pts[i].x, pts[i].y) < MOUSE_DISTANCE * MOUSE_DISTANCE) {
			curPoint = pts + i;
		}
	}
	
	// if doubleclick, reset
	if(ofDistSquared(x, y, lastPressPlace.x, lastPressPlace.y) < MOUSE_DISTANCE * MOUSE_DISTANCE && ofGetElapsedTimef() - lastPressTime < 0.25f) {
//		pts[0].set(0, 0);
//		pts[1].set(width, 0);
//		pts[2].set(width, height);
//		pts[3].set(0, height);
		if(curPoint) {
			switch((int)curPoint->z) {		// stores index of point 
				case 0: pts[0].set(0, 0); break;
				case 1:	pts[1].set(width, 0); break;
				case 2:	pts[2].set(width, height); break;
				case 3:	pts[3].set(0, height); break;
			}			
		}
	}
	
	lastPressPlace.set(x, y);
	lastPressTime = ofGetElapsedTimef();
}

void ofxSimpleGuiQuadWarp::onPressOutside(int x, int y, int button) {
	onPress(x, y, button);
}


void ofxSimpleGuiQuadWarp::onDragOver(int x, int y, int button) {
	if(curPoint) {
		curPoint->set(x - this->x, y - this->y);
	}
	
}

//---------------------------------------------------------------------
void ofxSimpleGuiQuadWarp::onDragOutside(int x, int y, int button) {
	onDragOver(x, y, button);
}



//---------------------------------------------------------------------
void ofxSimpleGuiQuadWarp::draw(float x, float y) {
	setPos(x, y);
	glPushMatrix();
	glTranslatef(x, y, 0);
	glColor3f(1, 1, 1);
	baseDraw->draw(0, 0);
	
	ofEnableAlphaBlending();
	ofFill();
	
	for(int i=0; i<4; i++) {
		if(curPoint == &pts[i]) {
			ofSetColor(255, 0, 0);
			ofCircle(pts[i].x, pts[i].y, 4);
		} else {
			ofSetColor(0, 255, 0);
			ofCircle(pts[i].x, pts[i].y, 2);
		}
			
	}
	
	
	ofBeginShape();
	ofNoFill();
	ofSetColor(255, 255, 255);
	for(int i=0; i<4; i++) {
		ofVertex(pts[i].x, pts[i].y);
	}
	ofEndShape(TRUE);
	ofDisableAlphaBlending();
	
	glPopMatrix();
}
