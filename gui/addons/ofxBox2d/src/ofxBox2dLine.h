

#pragma once
#include "ofMain.h"
#include "ofxBox2dBaseShape.h"

class ofxBox2dLine : public ofxBox2dBaseShape {
	
public:
	
	b2EdgeChainDef		edgeDef;
	b2PolygonDef		strip;
	vector <ofPoint>	points;
	bool				bShapeCreated;
	bool				bIsLoop;
	
	//------------------------------------------------
	
	ofxBox2dLine() {
		bShapeCreated = false;
		bIsLoop		  = false;
	}
	
	//------------------------------------------------
	void addPoint(float x, float y) {
		points.push_back(ofPoint(x, y));	
	}
	void addPoint(ofPoint p) {
		points.push_back(ofPoint(p.x, p.y));	
	}
	//------------------------------------------------
	void clear() {
		if(bShapeCreated) {
			for(int i=0; i<points.size(); i++) {
				points.erase(points.begin() + i);
			}
			points.clear();
			destroyShape();
			dead = false;
		}
	}
	
	//------------------------------------------------
	void createShape() {
		
		if(world == NULL) {
			ofLog(OF_LOG_NOTICE, "- must have a valid world -");
			return;
		}
		
		int numPoints = points.size();
		if(numPoints <= 0) return;
		
		b2Vec2 pts[numPoints];
		for(int i=0; i<numPoints; i++) {
			pts[i].Set(points[i].x/OFX_BOX2D_SCALE, points[i].y/OFX_BOX2D_SCALE);
		}	
		
		
		bodyDef.position.Set(0, 0);//b2dNum(ofGetWidth()/2), b2dNum(ofGetHeight()/2));
		body = world->CreateBody(&bodyDef);
		
		/*
		 b2CircleDef weight;
		 weight.filter.maskBits = 0x0000;
		 weight.density = 4.0f;
		 weight.radius = 0.5f;
		 weight.localPosition.Set(0, 0);
		 body->CreateShape(&weight);
		 */
		//type = e_unknownShape;
		//userData = NULL;
		edgeDef.friction = 0.2f;
		edgeDef.restitution = 0.96f;
		edgeDef.density = 1.0f;
		//filter.categoryBits = 0x0001;
		//filter.maskBits = 0xFFFF;
		//filter.groupIndex = 0;
		//isSensor = false;
		
		edgeDef.vertexCount = numPoints;
		edgeDef.vertices = pts;
		edgeDef.isALoop  = bIsLoop;
		body->CreateShape(&edgeDef);
		
		body->SetMassFromShapes();
		
		bShapeCreated = true;
		
		// anything that you need called
		init();
	}
	
	//------------------------------------------------
	void setup(b2World * b2dworld, float x1, float y1, float x2, float y2) {
		
		if(b2dworld == NULL) {
			ofLog(OF_LOG_NOTICE, "- must have a valid world -");
			return;
		}
		
		world				= b2dworld;
		
		
	}
	
	
	/*
	 //------------------------------------------------
	 float getRadius() {
	 b2Shape* shape		= body->GetShapeList();
	 b2CircleShape *data = (b2CircleShape*)shape;
	 return data->GetRadius() * OFX_BOX2D_SCALE;
	 }
	 
	 //------------------------------------------------
	 float getRotation() {
	 
	 const  b2XForm& xf	= body->GetXForm();
	 float  r			= getRadius()/OFX_BOX2D_SCALE;
	 b2Vec2 a			= xf.R.col1;
	 b2Vec2 p1			= body->GetPosition();
	 b2Vec2 p2			= p1 + r * a;
	 
	 float dx = p2.x+r/2 - p1.x+r/2;
	 float dy = p2.y - p1.y;
	 return ofRadToDeg(atan2(dy, dx));
	 
	 }
	 */
	
	
	//------------------------------------------------
	void draw() {
		/*
		 if(dead) return;
		 
		 //wow this is a pain
		 b2Shape* s = body->GetShapeList();
		 const b2XForm& xf = body->GetXForm();
		 b2PolygonShape* poly = (b2PolygonShape*)s;
		 int count = poly->GetVertexCount();
		 const b2Vec2* localVertices = poly->GetVertices();
		 b2Assert(count <= b2_maxPolygonVertices);
		 b2Vec2 verts[b2_maxPolygonVertices];
		 for(int32 i=0; i<count; ++i) {
		 verts[i] = b2Mul(xf, localVertices[i]);
		 }
		 
		 
		 ofSetColor(0, 255, 255);
		 glBegin(GL_LINE_LOOP);
		 for (int32 i = 0; i <count; i++) {
		 printf("%i",  i);
		 glVertex2f(verts[i].x*OFX_BOX2D_SCALE, verts[i].y*OFX_BOX2D_SCALE);
		 }
		 glEnd();*/
		
		ofBeginShape();
		ofSetColor(255, 0, 255);
		ofNoFill();
		for(int i=0; i<points.size(); i++) {
			ofVertex(points[i].x, points[i].y);
		}
		ofEndShape();
	}
	
};














