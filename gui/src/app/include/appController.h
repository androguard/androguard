#ifndef APPCONTROLLER_H
#define APPCONTROLLER_H

#include "appAndroGuard.h"
#include "ofxSimpleGuiToo.h"

class appController : public ofSimpleApp{
    public:
        appController();
        virtual ~appController();
        void setup();
        void mainLoop();
        void draw();
        void keyPressed(int);

        appAndroGuard   aAA;
        ofxSimpleGuiToo gui;
    protected:
    private:
};

#endif // APPCONTROLLER_H
