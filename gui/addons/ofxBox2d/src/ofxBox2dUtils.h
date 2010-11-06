#pragma once
#include "ofMain.h"
#include "Box2D.h"


#define OFX_BOX2D_SCALE 30.0f


static float b2dNum(float f) {
	return (float)f/OFX_BOX2D_SCALE;	
}
