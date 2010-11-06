#pragma once
#include "ofMain.h"
#include "Box2D.h"

class ofxBox2dRender : public b2DebugDraw {
	
public:
	
	float scaleFactor;
	
	void setScale(float f) {
		scaleFactor = f;
	}
	
	void DrawPolygon(const b2Vec2* vertices, int32 vertexCount, const b2Color& color) {
		ofSetColor(color.r*255.0, color.g*255.0, color.b*255.0);
		ofBeginShape();
		for (int i = 0; i < vertexCount; ++i) {
			ofVertex(vertices[i].x*OFX_BOX2D_SCALE, vertices[i].y*OFX_BOX2D_SCALE);
		}
		ofEndShape();
	}
	void DrawSolidPolygon(const b2Vec2* vertices, int32 vertexCount, const b2Color& color) {
		
		ofSetColor(0xffffff);
		ofBeginShape();
		for(int i=0; i<vertexCount; ++i) {
			ofVertex(vertices[i].x*OFX_BOX2D_SCALE, vertices[i].y*OFX_BOX2D_SCALE);
		}
		ofEndShape();
		
	
	}
	void DrawCircle(const b2Vec2& center, float32 radius, const b2Color& color) {
		const float32 k_segments = 16.0f;
		const float32 k_increment = 2.0f * b2_pi / k_segments;
		float32 theta = 0.0f;
		ofSetColor(color.r*255.0, color.g*255.0, color.b*255.0);
		ofBeginShape();
		for (int i = 0; i < k_segments; i++) {
			b2Vec2 v = center + radius * b2Vec2(cosf(theta), sinf(theta));
			ofVertex(v.x, v.y);
			theta += k_increment;
		}
		ofEndShape();
	}
	void DrawSolidCircle(const b2Vec2& center, float32 radius, const b2Vec2& axis, const b2Color& color) {
		const float32 k_segments    = 16.0f;
		const float32 k_increment   = 2.0f * b2_pi / k_segments;
		float32 theta			    = 0.0f;
		float rad = (radius*scaleFactor);
		glEnable(GL_BLEND);
		glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		ofSetColor(255, 255, 255, 200);
		ofFill();
		ofCircle(center.x*scaleFactor, center.y*scaleFactor, rad);
	}
	void DrawSegment(const b2Vec2& p1, const b2Vec2& p2, const b2Color& color) {
		ofSetColor(255, 255, 255, 200);
		ofLine(p1.x*OFX_BOX2D_SCALE, p1.y*OFX_BOX2D_SCALE, p2.x*OFX_BOX2D_SCALE, p2.y*OFX_BOX2D_SCALE);
	}
	void DrawXForm(const b2XForm& xf) {
	}
	void DrawPoint(const b2Vec2& p, float32 size, const b2Color& color) {
	}
	void DrawString(int x, int y, const char* string, ...) {
	}
	void DrawAABB(b2AABB* aabb, const b2Color& color) {
		ofSetColor(color.r*255.0, color.g*255.0, color.b*255.0);
		ofBeginShape();
		ofVertex(aabb->lowerBound.x, aabb->lowerBound.y);
		ofVertex(aabb->upperBound.x, aabb->lowerBound.y);
		ofVertex(aabb->upperBound.x, aabb->upperBound.y);
		ofVertex(aabb->lowerBound.x, aabb->upperBound.y);
		ofEndShape();
	}
	
};