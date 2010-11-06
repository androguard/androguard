#ifndef APPCONTROLLER_H
#define APPCONTROLLER_H

//#include "baseGui.h"
#include "ofxSimpleGuiToo.h"
#include "ofxBox2d.h"

class appController : public ofSimpleApp{
    public:
        appController();
        virtual ~appController();
        void setup();
        void mainLoop();
        void draw();
        void keyPressed(int);

        vector          <ofxBox2dCircle>        circles;
        ofxBox2d box2d;
        ofxBox2dLine                                    lineStrip;                //    a linestrip for drawing

        ofxSimpleGuiToo gui;
    protected:
    private:
};

#endif // APPCONTROLLER_H
