/*
* Copyright (c) 2006-2007 Erin Catto http://www.gphysics.com
*
* This software is provided 'as-is', without any express or implied
* warranty.  In no event will the authors be held liable for any damages
* arising from the use of this software.
* Permission is granted to anyone to use this software for any purpose,
* including commercial applications, and to alter it and redistribute it
* freely, subject to the following restrictions:
* 1. The origin of this software must not be misrepresented; you must not
* claim that you wrote the original software. If you use this software
* in a product, an acknowledgment in the product documentation would be
* appreciated but is not required.
* 2. Altered source versions must be plainly marked as such, and must not be
* misrepresented as being the original software.
* 3. This notice may not be removed or altered from any source distribution.
*/

#ifndef B2_EDGE_SHAPE_H
#define B2_EDGE_SHAPE_H

#include "b2Shape.h"

/// This structure is used to build circle shapes.
struct b2EdgeChainDef : public b2ShapeDef
{
	b2EdgeChainDef()
	{
		type = e_edgeShape;
		vertexCount = 0;
		isALoop = true;
		vertices = NULL;
	}
	/// The vertices in local coordinates. You must manage the memory
	/// of this array on your own, outside of Box2D. 
	b2Vec2* vertices;
	
	/// The number of vertices in the chain. 
	int32 vertexCount;
	
	/// Whether to create an extra edge between the first and last vertices:
	bool isALoop;
};

/// A circle shape.
class b2EdgeShape : public b2Shape
{
public:
	/// @see b2Shape::TestPoint
	bool TestPoint(const b2XForm& transform, const b2Vec2& p) const;

	/// @see b2Shape::TestSegment
	b2SegmentCollide TestSegment(	const b2XForm& transform,
						float32* lambda,
						b2Vec2* normal,
						const b2Segment& segment,
						float32 maxLambda) const;

	/// @see b2Shape::ComputeAABB
	void ComputeAABB(b2AABB* aabb, const b2XForm& transform) const;

	/// @see b2Shape::ComputeSweptAABB
	void ComputeSweptAABB(	b2AABB* aabb,
							const b2XForm& transform1,
							const b2XForm& transform2) const;

	/// @see b2Shape::ComputeMass
	void ComputeMass(b2MassData* massData) const;

	/// @warning This only gives a consistent and sensible answer when when summed over a body only contains loops of edges
	/// @see b2Shape::ComputeSubmergedArea
	float32 ComputeSubmergedArea(	const b2Vec2& normal,
									float32 offset,
									const b2XForm& xf, 
									b2Vec2* c) const;
	
	/// Linear distance from vertex1 to vertex2:
	float32 GetLength() const;

	/// Local position of vertex in parent body
	const b2Vec2& GetVertex1() const;

	/// Local position of vertex in parent body
	const b2Vec2& GetVertex2() const;

	/// "Core" vertex with TOI slop for b2Distance functions:
	const b2Vec2& GetCoreVertex1() const;

	/// "Core" vertex with TOI slop for b2Distance functions:
	const b2Vec2& GetCoreVertex2() const;
	
	/// Perpendicular unit vector point, pointing from the solid side to the empty side: 
	const b2Vec2& GetNormalVector() const;
	
	/// Parallel unit vector, pointing from vertex1 to vertex2:
	const b2Vec2& GetDirectionVector() const;
	
	const b2Vec2& GetCorner1Vector() const;
	
	const b2Vec2& GetCorner2Vector() const;
	
	bool Corner1IsConvex() const;
	
	bool Corner2IsConvex() const;

	b2Vec2 GetFirstVertex(const b2XForm& xf) const;

	b2Vec2 Support(const b2XForm& xf, const b2Vec2& d) const;
	
	/// Get the next edge in the chain.
	b2EdgeShape* GetNextEdge() const;
	
	/// Get the previous edge in the chain.
	b2EdgeShape* GetPrevEdge() const;

	void SetPrevEdge(b2EdgeShape* edge, const b2Vec2& core, const b2Vec2& cornerDir, bool convex);
	void SetNextEdge(b2EdgeShape* edge, const b2Vec2& core, const b2Vec2& cornerDir, bool convex);
	
private:

	friend class b2Shape;
	friend class b2Body;

	b2EdgeShape(const b2Vec2& v1, const b2Vec2& v2, const b2ShapeDef* def);

	void UpdateSweepRadius(const b2Vec2& center);

	b2Vec2 m_v1;
	b2Vec2 m_v2;
	
	b2Vec2 m_coreV1;
	b2Vec2 m_coreV2;
	
	float32 m_length;
	
	b2Vec2 m_normal;
	
	b2Vec2 m_direction;
	
	// Unit vector halfway between m_direction and m_prevEdge.m_direction:
	b2Vec2 m_cornerDir1;
	
	// Unit vector halfway between m_direction and m_nextEdge.m_direction:
	b2Vec2 m_cornerDir2;
	
	bool m_cornerConvex1;
	bool m_cornerConvex2;
	
	b2EdgeShape* m_nextEdge;
	b2EdgeShape* m_prevEdge;
};

inline float32 b2EdgeShape::GetLength() const
{
	return m_length;
}

inline const b2Vec2& b2EdgeShape::GetVertex1() const
{
	return m_v1;
}

inline const b2Vec2& b2EdgeShape::GetVertex2() const
{
	return m_v2;
}

inline const b2Vec2& b2EdgeShape::GetCoreVertex1() const
{
	return m_coreV1;
}

inline const b2Vec2& b2EdgeShape::GetCoreVertex2() const
{
	return m_coreV2;
}

inline const b2Vec2& b2EdgeShape::GetNormalVector() const
{
	return m_normal;
}

inline const b2Vec2& b2EdgeShape::GetDirectionVector() const
{
	return m_direction;
}

inline const b2Vec2& b2EdgeShape::GetCorner1Vector() const
{
	return m_cornerDir1;
}

inline const b2Vec2& b2EdgeShape::GetCorner2Vector() const
{
	return m_cornerDir2;
}

inline b2EdgeShape* b2EdgeShape::GetNextEdge() const
{
	return m_nextEdge;
}

inline b2EdgeShape* b2EdgeShape::GetPrevEdge() const
{
	return m_prevEdge;
}

inline b2Vec2 b2EdgeShape::GetFirstVertex(const b2XForm& xf) const
{
	return b2Mul(xf, m_coreV1);
}

inline bool b2EdgeShape::Corner1IsConvex() const
{
	return m_cornerConvex1;
}

inline bool b2EdgeShape::Corner2IsConvex() const
{
	return m_cornerConvex2;
}
#endif
