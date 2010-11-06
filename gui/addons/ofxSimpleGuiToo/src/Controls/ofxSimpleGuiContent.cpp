
#include "ofxSimpleGuiContent.h"


ofxSimpleGuiContent::ofxSimpleGuiContent(string name, ofBaseDraws& content, float fixwidth) : ofxSimpleGuiControl(name) {
	this->content = &content;
	this->fixwidth  = fixwidth;
	controlType = "Content";
	setup();
}

void ofxSimpleGuiContent::setup() {
	fixheight = fixwidth * content->getHeight()/content->getWidth();
	setSize(fixwidth, fixheight + config->sliderTextHeight);
}

void ofxSimpleGuiContent::draw(float x, float y) {
	if(content->getWidth() == 0 && content->getHeight() ==0) return;
	
	setPos(x, y);
	setup();
	
	glPushMatrix();
	glTranslatef(x, y, 0);
	ofEnableAlphaBlending();
	ofFill();
	glColor4f(0, 0, 0, 0.8f);
	ofRect(0, 0, width, fixheight);
	
	ofSetColor(0xffffff);
	content->draw(0, 0, width, fixheight);
	
	ofFill();
	setTextBGColor();
	ofRect(0, fixheight, width, config->sliderTextHeight);
	
	setTextColor();
	ofDrawBitmapString(name, 3, fixheight + 15);
	ofDisableAlphaBlending();
	glPopMatrix();
}
