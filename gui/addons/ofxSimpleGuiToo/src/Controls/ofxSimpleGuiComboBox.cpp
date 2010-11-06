/*
 *  ofxSimpleGuiComboBox.cpp
 *  AlgorhythmicSorting
 *
 *  Created by Administrator on 7/2/10.
 *  Copyright 2010 __MyCompanyName__. All rights reserved.
 *
 */

#include "ofxSimpleGuiComboBox.h"
#include "ofxSimpleGuiPage.h"

#define kMaxChoiceStringLen 150
#define kMaxNameStringLen 100

ofxSimpleGuiComboBox::ofxSimpleGuiComboBox(string name, int &choice_out, int numChoices, ofxSimpleGuiPage *owner, string* choiceTitles ) :
ofxSimpleGuiControl(name),
m_selectedChoice(choice_out),
m_page(owner)
{
	m_selectedChoice = m_mouseChoice = 0;
	if(numChoices <=1)
		numChoices = 1;
	m_hasFocus=false;
	m_title = name;
	
	for(int i=0; i<numChoices; i++){
		addChoice(choiceTitles ? choiceTitles[i] : ofToString(i));
	}
	controlType = "ComboBox";
	setup();
}


ofxSimpleGuiComboBox::~ofxSimpleGuiComboBox() {
}


void ofxSimpleGuiComboBox::setTitleForIndex(int index, string title) {
	if(index < 0 || index >= m_choices.size()) return;
	m_choices[index] = title;
}

string ofxSimpleGuiComboBox::getTitleForIndex(int index) {
	if(index < 0 || index >= m_choices.size())return m_choices.size() ? m_choices[m_selectedChoice] : "No Choices Available";
	return m_choices[index];
}


void ofxSimpleGuiComboBox::addChoice(string title, int index) {
	int insertIndex = m_choices.size();
	
	if(index >= 0 && index < m_choices.size()) insertIndex = index;
	
	m_choices.insert(m_choices.begin() + insertIndex, title);
}


int ofxSimpleGuiComboBox::getIndexForTitle(string title) {
	for(int i=0; i<m_choices.size(); i++) {
		if(title.compare(m_choices[i]) == 0) return i;
	}
	return -1;
}

void ofxSimpleGuiComboBox::removeChoice(string title) {
	int index = getIndexForTitle(title);
	if(index >= 0) removeChoice(index);
}

void ofxSimpleGuiComboBox::removeChoice(int index) {
	int removeIndex = m_choices.size() - 1;
	if(index >= 0 && index < m_choices.size())
		removeIndex = index;
	
	m_choices.erase(m_choices.begin() + removeIndex);
	//also update the selected indexes.
	if(m_selectedChoice >= removeIndex)
		m_selectedChoice--;
	if(m_mouseChoice >= removeIndex)
		m_mouseChoice--;
}

void ofxSimpleGuiComboBox::setup() {
	setSize(config->gridSize.x - config->padding.x, config->comboBoxHeight);
}

void ofxSimpleGuiComboBox::loadFromXML(ofxXmlSettings &XML) {
	setValue(XML.getValue(controlType + "_" + key + ":value", 0));
}

void ofxSimpleGuiComboBox::saveToXML(ofxXmlSettings &XML) {
	XML.addTag(controlType + "_" + key);
	XML.pushTag(controlType + "_" + key);
	XML.addValue("name", name);
	XML.addValue("value", getValue());
	XML.popTag();
}

void ofxSimpleGuiComboBox::keyPressed( int key ) {
}

int ofxSimpleGuiComboBox::getValue() {
	return m_selectedChoice;
}

void ofxSimpleGuiComboBox::setValue(int index) {
	m_selectedChoice = ofClamp(index, 0, m_choices.size());
}

void ofxSimpleGuiComboBox::setValue(string title) {
	setValue(getIndexForTitle(title));
}


//press was outside - handle.
void onPressOutside(int x, int y, int button)	{
	
}

void ofxSimpleGuiComboBox::onPress(int x, int y, int button) {
//	beenPressed = true;
	m_mouseMovedSinceClick=false;
	//a click toggles focus state if we are off
	if(!m_hasFocus) {
		//expand the height for all choices
		//      setSize(config->gridSize.x - config->padding.x, config->comboBoxHeight * m_choices.size());
		m_hasFocus = true;
		//notify that we want to steal all events from the page
		m_page->SetEventStealingControl(*this);
	} else {
		//if we have focus, a click signals that we should lose it
		releaseEventStealingFocus();
	}
}

void ofxSimpleGuiComboBox::onPressOutside(int x, int y, int button){
	if(m_hasFocus)
		releaseEventStealingFocus();
}


void ofxSimpleGuiComboBox::onDragOver(int x, int y, int button){
	//same behavior as mouse move
	onMouseMove(x,y);
}

void ofxSimpleGuiComboBox::onDragOutside(int x, int y, int button){
	//same behavior as mouse move
	onMouseMove(x,y);
}

bool ofxSimpleGuiComboBox::hitTest(int tx, int ty) {
	if(!m_hasFocus) 
		return ofxMSAInteractiveObject::hitTest(tx,ty);
	
	int fullheight = height + config->comboBoxTextHeight * m_choices.size();  
	
	return ((tx > x) && (tx < x + width) && (ty > y) && (ty < y + fullheight));
}

void ofxSimpleGuiComboBox::onMouseMove(int x, int y) {
	m_mouseMovedSinceClick=true;
	if(m_hasFocus) {
		//see which index was selected.
		float fChoice = (y - (height - config->comboBoxTextHeight) - (this->y + config->comboBoxTextHeight))/config->comboBoxTextHeight;
		//TODO:replace with OF constrain macro.
		m_mouseChoice = fChoice < 0?-1:(fChoice>= m_choices.size()? -1:fChoice);
	}
}

void ofxSimpleGuiComboBox::onReleaseOutside(int x, int y, int button) {
	onRelease(x, y, button);
}

void ofxSimpleGuiComboBox::onRelease(int x, int y, int button) {
	if(m_hasFocus && m_mouseMovedSinceClick) {
		releaseEventStealingFocus();
	}
}

void ofxSimpleGuiComboBox::releaseEventStealingFocus(){
	//see which index was selected, but only if the user actually moved around.
	m_selectedChoice = m_mouseChoice >= 0? m_mouseChoice : m_selectedChoice;
	
	//a release toggles focus state if we are on - TODO: unless x and y don't change
	m_hasFocus = false;
	//      setSize(config->gridSize.x - config->padding.x, config->comboBoxHeight);
	//also let the page know we don't need to steal all the events and draw over anymore
	m_page->ReleaseEventStealingControl();
}

//special overloads - this is a hack - later think about making ofxSimpleGuiControl's methods virtual.
void ofxSimpleGuiComboBox::setCBTextColor() {
	if(m_hasFocus) ofSetColor(config->textOverColor);
	else ofSetColor(config->textColor);
}

void ofxSimpleGuiComboBox::setCBTextBGColor() {
	if(m_hasFocus) ofSetColor(config->textBGOverColor);
	else ofSetColor(config->textBGColor);
}


#define kSGCBTriangleWidth   10
#define KSGCBTrianglePadding 5
#define kSGCBTextPaddingX    3
#define kSGCBTextPaddingY    15
void ofxSimpleGuiComboBox::draw(float x, float y) {
	//we assume a max of 256 characters.
	char choiceBuf[256];
	
	setPos(x, y);
	
	glPushMatrix();
	glTranslatef(x, y, 0);
	
	ofEnableAlphaBlending();
	ofFill();
	setTextBGColor();
	ofRect(0, 0, width, height);
	
	setTextColor();
//	sprintf(choiceBuf, "%s: %s", m_title, m_choices.size() ? m_choices[m_selectedChoice] : "(No Choices Available)");
	
	ofDrawBitmapString(m_title + "\n\n" + (m_choices.size() ? m_choices[m_selectedChoice] : "N/A"), kSGCBTextPaddingX, kSGCBTextPaddingY);
	//draw a combobox down triangle icon so the users know to click
	ofTriangle(width - (kSGCBTriangleWidth + KSGCBTrianglePadding), kSGCBTextPaddingY/2,
			   width - (KSGCBTrianglePadding), kSGCBTextPaddingY/2,
			   width - (kSGCBTriangleWidth/2 + KSGCBTrianglePadding), kSGCBTextPaddingY);
	
	if(m_hasFocus) {
		setCBTextBGColor();
		ofRect(0, height, width, config->comboBoxTextHeight * m_choices.size());
		setTextColor();
		ofLine(0, config->comboBoxHeight-1, width, config->comboBoxHeight-1);
		
		for(int i=0; i < m_choices.size(); i++) {
			setCBTextColor();
			//invert for selected choice
			float curY = height + i*config->comboBoxTextHeight; 
			if(i==m_mouseChoice){
				//draw a text colored rect so we can see the inverse
				ofRect(0, curY, width, config->comboBoxTextHeight);
				setCBTextBGColor();
			}
			
			ofDrawBitmapString(m_choices[i], kSGCBTextPaddingX, curY + kSGCBTextPaddingY);
		}
	}
	ofDisableAlphaBlending();
	
	glPopMatrix();
}
