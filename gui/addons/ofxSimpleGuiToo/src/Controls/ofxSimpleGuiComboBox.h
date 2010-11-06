/*
 *  ofxSimpleGuiComboBox.h
 *  open frameworks simpleguitoo
 *
 *  Created by Michael Chinen on 7/2/10.
 *
 */

#pragma once

#include "ofxSimpleGuiControl.h"


class ofxSimpleGuiPage;

class ofxSimpleGuiComboBox : public ofxSimpleGuiControl {
public:
	//create a combo box which displays "Name : selection"
	//choiceTitles is an array of strings that can be NULL in which case numbers will be used to display the choices
	//the titles can be movified later with the below documented add/set/removeChoice methods
	ofxSimpleGuiComboBox(string name, int &choice_out, int numChoices,  ofxSimpleGuiPage *owner, string* choiceTitles = NULL ) ;
	virtual ~ofxSimpleGuiComboBox();
	
	void setup();
	void loadFromXML(ofxXmlSettings &XML);
	void saveToXML(ofxXmlSettings &XML);
	void keyPressed( int key );
	void onPress(int x, int y, int button);
	void onRelease(int x, int y, int button);
	void onReleaseOutside(int x, int y, int button);
	void draw(float x, float y);
	
	//returns the selected index number of the current choice
	int  getValue();
	
	// set the current selected choice to number
	void setValue(int index);
	
	// set the current selected to text
	void setValue(string title);
	
	
	// get index for title
	int getIndexForTitle(string title);
	
	//Changes the title of a choice index.  index must be valid.
	void setTitleForIndex(int index, string title);
	
	//Get the current choice title an invalid index (default is -1),
	//Otherwise get the title of the index asked for.
	string getTitleForIndex(int index = -1);
	
	//Add a new choice with a specified title.
	//If an invalid index (default = -1) is used then append to the end.
	//If an invalid title is supplied, then the title is set to the index number of the new choice.
	void addChoice(string title = NULL, int index = -1);
	
	//convenience function to remove by a string match.  removes the first index that matches
	void removeChoice(string title);

	//remove a choice at specified index
	//invalid index (default = -1) will remove the last choice in the combo box
	void removeChoice(int index = -1);
	
	virtual void onPressOutside(int x, int y, int button);
	virtual void onMouseMove(int x, int y);
	virtual void onDragOver(int x, int y, int button);
	virtual void onDragOutside(int x, int y, int button);
	
	virtual bool hitTest(int tx, int ty);
	
protected:
	void setCBTextColor();
	void setCBTextBGColor();
	void releaseEventStealingFocus();
	
	int            m_mouseChoice;
	int            &m_selectedChoice;
	bool           m_hasFocus;
	bool           m_mouseMovedSinceClick;
	string          m_title;
	vector<string>  m_choices;
	ofxSimpleGuiPage* m_page;
};
