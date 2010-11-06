#pragma once

#include "ofxBox2d.h"

class ofxBox2dSoftBody : public ofxBox2dBaseShape {
	
	
public:
	
	int							ringSize;
	ofxBox2dCircle				center;
	
	vector <b2Joint*>			m_joints;
	vector <ofxBox2dCircle*>	ring;
	vector <b2Joint*>			center_joints;
	
	// ------------------------------------------------
	
	ofxBox2dSoftBody() {
		
	}
	
	// ------------------------------------------------
	void setup(b2World * world, float px, float py) {
		
		if(world == NULL) {
			ofLog(OF_LOG_NOTICE, "- need a valid world -");
			return;
		}
		bool fix = false;
		
		ringSize = (int)ofRandom(10, 20);
		float size = ofRandom(5, 10);
		
		float ringRadius = size*ringSize/2;
		
		float f  = 29.4;
		float dr = .02;
		int ringCount = 0;
		
		//ring = new ofxBox2dCircle[ringSize];
		//m_joints = new  b2Joint[ringSize];
		//center_joints = new b2Joint[ringSize];
		
		//in the center
		center.setPhysics(1.0, 0.0, 0.0);
		center.setup(world, px, py, size, fix);
		
		// ------------- outter ring
		ofPoint p;
		float angle		 = 0.0f;
		float angleAdder = M_TWO_PI / (float)ringSize;
		for(int i=0; i<ringSize; i++) {
			
			p.x = cos(angle) * ringRadius;
			p.y = sin(angle) * ringRadius;
			
			angle += angleAdder;
			
			
			ring.push_back(new ofxBox2dCircle());
			ring.back()->setPhysics(5.0, 0.60, 0.0);
			ring.back()->setup(world, px+p.x, py+p.y, size, fix);
			
			if(i > 0) {
				b2DistanceJointDef jd;
				b2Vec2 p1, p2, d;
				
				jd.frequencyHz = f;
				jd.dampingRatio = dr;
				
				jd.body1 = ring[i-1]->body;
				jd.body2 = ring[i]->body;
				
				jd.localAnchor1.Set(0, 0);
				jd.localAnchor2.Set(0, 0);
				jd.collideConnected = true;
				
				p1 = jd.body1->GetWorldPoint(jd.localAnchor1);
				p2 = jd.body2->GetWorldPoint(jd.localAnchor2);
				d = p2 - p1;
				jd.length = d.Length();
				
				//m_joints[i] = 
				b2Joint * bb;
				m_joints.push_back(bb);
				m_joints.back() = world->CreateJoint(&jd);
			}
			
			if(i == ringSize-1) {
				printf("i is 9");
				b2DistanceJointDef jd;
				b2Vec2 p1, p2, d;
				
				jd.frequencyHz = f;
				jd.dampingRatio = dr;
				
				jd.body1 = ring[0]->body;
				jd.body2 = ring[ringSize-1]->body;
				
				jd.localAnchor1.Set(0, 0);
				jd.localAnchor2.Set(0, 0);
				jd.collideConnected = true;
				
				p1 = jd.body1->GetWorldPoint(jd.localAnchor1);
				p2 = jd.body2->GetWorldPoint(jd.localAnchor2);
				d = p2 - p1;
				jd.length = d.Length();
				
				b2Joint * bb;
				m_joints.push_back(bb);
				m_joints.back() = world->CreateJoint(&jd);
			}
			ringCount ++;
		}
		
		
		// ------------- inner ring
		p = 0;
		angle		 = 0.0f;
		angleAdder = M_TWO_PI / (float)ringSize;
		float sm = 1.6;
		for(int i=0; i<ringSize; i++) {
			
			p.x = cos(angle) * ringRadius/sm;
			p.y = sin(angle) * ringRadius/sm;
			
			angle += angleAdder;
			
			
			ring.push_back(new ofxBox2dCircle());
			ring.back()->setPhysics(1.0, 0.0, 0.0);
			ring.back()->setup(world, px+p.x, py+p.y, size, fix);
			
			if(i > 0) {
				b2DistanceJointDef jd;
				b2Vec2 p1, p2, d;
				
				jd.frequencyHz = f;
				jd.dampingRatio = dr;
				
				jd.body1 = ring[ringCount-1]->body;
				jd.body2 = ring[ringCount]->body;
				
				jd.localAnchor1.Set(0, 0);
				jd.localAnchor2.Set(0, 0);
				jd.collideConnected = true;
				
				p1 = jd.body1->GetWorldPoint(jd.localAnchor1);
				p2 = jd.body2->GetWorldPoint(jd.localAnchor2);
				d = p2 - p1;
				jd.length = d.Length();
				
				//m_joints[i] = 
				b2Joint * bb;
				m_joints.push_back(bb);
				m_joints.back() = world->CreateJoint(&jd);
			}
			
			if(i == ringSize-1) {
				b2DistanceJointDef jd;
				b2Vec2 p1, p2, d;
				
				jd.frequencyHz = f;
				jd.dampingRatio = dr;
				
				jd.body1 = ring[ringSize]->body;
				jd.body2 = ring[ringCount]->body;
				
				jd.localAnchor1.Set(0, 0);
				jd.localAnchor2.Set(0, 0);
				jd.collideConnected = true;
				
				p1 = jd.body1->GetWorldPoint(jd.localAnchor1);
				p2 = jd.body2->GetWorldPoint(jd.localAnchor2);
				d = p2 - p1;
				jd.length = d.Length();
				
				//m_joints[i] = 
				b2Joint * bb;
				m_joints.push_back(bb);
				m_joints.back() = world->CreateJoint(&jd);
			}
			
			ringCount ++;
		}
		
		// -------------- in out joints
		for(int i=0; i<ringSize; i++) {
			
			b2DistanceJointDef jd;
			b2Vec2 p1, p2, d;
			
			jd.frequencyHz = f;
			jd.dampingRatio = dr;
			
			jd.body1 = ring[i]->body;
			jd.body2 = ring[(ringSize+i)]->body;
			
			jd.localAnchor1.Set(0, 0);
			jd.localAnchor2.Set(0, 0);
			jd.collideConnected = true;
			
			p1 = jd.body1->GetWorldPoint(jd.localAnchor1);
			p2 = jd.body2->GetWorldPoint(jd.localAnchor2);
			d = p2 - p1;
			jd.length = d.Length();
			
			//m_joints[i] = 
			b2Joint * bb;
			m_joints.push_back(bb);
			m_joints.back() = world->CreateJoint(&jd);
		}
		
		// -------------- cross joints
		for(int i=0; i<ringSize; i++) {
			if(i < ringSize-1) {
				b2DistanceJointDef jd;
				b2Vec2 p1, p2, d;
				
				jd.frequencyHz = f;
				jd.dampingRatio = dr;
				
				jd.body1 = ring[i]->body;
				jd.body2 = ring[(ringSize+i)+1]->body;
				
				jd.localAnchor1.Set(0, 0);
				jd.localAnchor2.Set(0, 0);
				jd.collideConnected = true;
				
				p1 = jd.body1->GetWorldPoint(jd.localAnchor1);
				p2 = jd.body2->GetWorldPoint(jd.localAnchor2);
				d = p2 - p1;
				jd.length = d.Length();
				
				//m_joints[i] = 
				b2Joint * bb;
				m_joints.push_back(bb);
				m_joints.back() = world->CreateJoint(&jd);
			}
			//connect the last joint
			if(i == ringSize-1) {
				b2DistanceJointDef jd;
				b2Vec2 p1, p2, d;
				
				jd.frequencyHz = f;
				jd.dampingRatio = dr;
				
				jd.body1 = ring[i]->body;
				jd.body2 = ring[ringSize]->body;
				
				jd.localAnchor1.Set(0, 0);
				jd.localAnchor2.Set(0, 0);
				jd.collideConnected = true;
				
				p1 = jd.body1->GetWorldPoint(jd.localAnchor1);
				p2 = jd.body2->GetWorldPoint(jd.localAnchor2);
				d = p2 - p1;
				jd.length = d.Length();
				
				//m_joints[i] = 
				b2Joint * bb;
				m_joints.push_back(bb);
				m_joints.back() = world->CreateJoint(&jd);
				
			}
		}
		
		
		//center joints
		for(int i=0; i<ringSize; i++) {
			
			b2DistanceJointDef jd;
			b2Vec2 p1, p2, d;
			
			jd.frequencyHz  = 5.4;
			jd.dampingRatio = dr;
			
			jd.body1 = ring[ringSize + i]->body;
			jd.body2 = center.body;
			
			jd.localAnchor1.Set(0, 0);
			jd.localAnchor2.Set(0, 0);
			jd.collideConnected = true;
			
			p1 = jd.body1->GetWorldPoint(jd.localAnchor1);
			p2 = jd.body2->GetWorldPoint(jd.localAnchor2);
			d = p2 - p1;
			jd.length = d.Length();
			
			b2Joint * bb;
			center_joints.push_back(bb);
			center_joints.back() = world->CreateJoint(&jd); 
		}
		
		
		
		b2FilterData data;
		data.groupIndex = 1;
		for(int i=0; i<ring.size(); i++) {
			
			b2FilterData data;
			data.categoryBits = 0x0003;
			data.groupIndex = 1;
			//ring[i]->setFilterData(data);
		}
		
		//center.setFilterData(data);
		
		// anything that you need called
		init();
	}
	
	// ------------------------------------------------
	void draw() {
		ofEnableAlphaBlending();
		ofSetColor(0, 233, 255, 100);
		for(int i=0; i<ring.size(); i++) {
			ring[i]->draw();
		}	
		
		ofSetColor(255, 233, 255, 100);
		
		for(int i=0; i<m_joints.size(); i++) {
			b2Vec2 p1 = m_joints[i]->GetAnchor1();
			b2Vec2 p2 = m_joints[i]->GetAnchor2();
			p1 *= OFX_BOX2D_SCALE;
			p2 *= OFX_BOX2D_SCALE;
			ofLine(p1.x, p1.y, p2.x, p2.y);	   
		}
		
		for(int i=0; i<center_joints.size(); i++) {
			b2Vec2 p1 = center_joints[i]->GetAnchor1();
			b2Vec2 p2 = center_joints[i]->GetAnchor2();
			p1 *= OFX_BOX2D_SCALE;
			p2 *= OFX_BOX2D_SCALE;
			ofLine(p1.x, p1.y, p2.x, p2.y);	   
		}
		ofDisableAlphaBlending();
		
		
		center.draw();
	}
	
};