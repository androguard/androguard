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

#include "b2EdgeShape.h"

b2EdgeShape::b2EdgeShape(const b2Vec2& v1, const b2Vec2& v2, const b2ShapeDef* def)
: b2Shape(def)
{
	b2Assert(def->type == e_edgeShape);

	m_type = e_edgeShape;
	
	m_prevEdge = NULL;
	m_nextEdge = NULL;
	
	m_v1 = v1;
	m_v2 = v2;
	
	m_direction = m_v2 - m_v1;
	m_length = m_direction.Normalize();
	m_normal.Set(m_direction.y, -m_direction.x);
	
	m_coreV1 = -b2_toiSlop * (m_normal - m_direction) + m_v1;
	m_coreV2 = -b2_toiSlop * (m_normal + m_direction) + m_v2;
	
	m_cornerDir1 = m_normal;
	m_cornerDir2 = -1.0f * m_normal;
}

void b2EdgeShape::UpdateSweepRadius(const b2Vec2& center)
{
	// Update the sweep radius (maximum radius) as measured from
	// a local center point.
	b2Vec2 d = m_coreV1 - center;
	float32 d1 = b2Dot(d,d);
	d = m_coreV2 - center;
	float32 d2 = b2Dot(d,d);
	m_sweepRadius = b2Sqrt(d1 > d2 ? d1 : d2);
}

bool b2EdgeShape::TestPoint(const b2XForm& transform, const b2Vec2& p) const
{
	B2_NOT_USED(transform);
	B2_NOT_USED(p);
	return false;
}

b2SegmentCollide b2EdgeShape::TestSegment(const b2XForm& transform,
								float32* lambda,
								b2Vec2* normal,
								const b2Segment& segment,
								float32 maxLambda) const
{
	b2Vec2 r = segment.p2 - segment.p1;
	b2Vec2 v1 = b2Mul(transform, m_v1);
	b2Vec2 d = b2Mul(transform, m_v2) - v1;
	b2Vec2 n = b2Cross(d, 1.0f);

	const float32 k_slop = 100.0f * B2_FLT_EPSILON;
	float32 denom = -b2Dot(r, n);

	// Cull back facing collision and ignore parallel segments.
	if (denom > k_slop)
	{
		// Does the segment intersect the infinite line associated with this segment?
		b2Vec2 b = segment.p1 - v1;
		float32 a = b2Dot(b, n);

		if (0.0f <= a && a <= maxLambda * denom)
		{
			float32 mu2 = -r.x * b.y + r.y * b.x;

			// Does the segment intersect this segment?
			if (-k_slop * denom <= mu2 && mu2 <= denom * (1.0f + k_slop))
			{
				a /= denom;
				n.Normalize();
				*lambda = a;
				*normal = n;
				return e_hitCollide;
			}
		}
	}

	return e_missCollide;
}

void b2EdgeShape::ComputeAABB(b2AABB* aabb, const b2XForm& transform) const
{
	b2Vec2 v1 = b2Mul(transform, m_v1);
	b2Vec2 v2 = b2Mul(transform, m_v2);
	aabb->lowerBound = b2Min(v1, v2);
	aabb->upperBound = b2Max(v1, v2);
}

void b2EdgeShape::ComputeSweptAABB(b2AABB* aabb, const b2XForm& transform1, const b2XForm& transform2) const
{
	b2Vec2 v1 = b2Mul(transform1, m_v1);
	b2Vec2 v2 = b2Mul(transform1, m_v2);
	b2Vec2 v3 = b2Mul(transform2, m_v1);
	b2Vec2 v4 = b2Mul(transform2, m_v2);
	aabb->lowerBound = b2Min(b2Min(b2Min(v1, v2), v3), v4);
	aabb->upperBound = b2Max(b2Max(b2Max(v1, v2), v3), v4);
}

void b2EdgeShape::ComputeMass(b2MassData* massData) const
{
	massData->mass = 0;
	massData->center = m_v1;

	// inertia about the local origin
	massData->I = 0;
}

b2Vec2 b2EdgeShape::Support(const b2XForm& xf, const b2Vec2& d) const
{
	b2Vec2 v1 = b2Mul(xf, m_coreV1);
	b2Vec2 v2 = b2Mul(xf, m_coreV2);
	return b2Dot(v1, d) > b2Dot(v2, d) ? v1 : v2;
}

void b2EdgeShape::SetPrevEdge(b2EdgeShape* edge, const b2Vec2& core, const b2Vec2& cornerDir, bool convex)
{
	m_prevEdge = edge;
	m_coreV1 = core;
	m_cornerDir1 = cornerDir;
	m_cornerConvex1 = convex;
}

void b2EdgeShape::SetNextEdge(b2EdgeShape* edge, const b2Vec2& core, const b2Vec2& cornerDir, bool convex)
{
	m_nextEdge = edge;
	m_coreV2 = core;
	m_cornerDir2 = cornerDir;
	m_cornerConvex2 = convex;
}

float32 b2EdgeShape::ComputeSubmergedArea(	const b2Vec2& normal,
												float32 offset,
												const b2XForm& xf, 
												b2Vec2* c) const
{
	//Note that v0 is independant of any details of the specific edge
	//We are relying on v0 being consistent between multiple edges of the same body
	b2Vec2 v0 = offset * normal;
	//b2Vec2 v0 = xf.position + (offset - b2Dot(normal, xf.position)) * normal;

	b2Vec2 v1 = b2Mul(xf, m_v1);
	b2Vec2 v2 = b2Mul(xf, m_v2);

	float32 d1 = b2Dot(normal, v1) - offset;
	float32 d2 = b2Dot(normal, v2) - offset;

	if(d1>0)
	{
		if(d2>0)
		{
			return 0;
		}
		else
		{
			v1 = -d2 / (d1 - d2) * v1 + d1 / (d1 - d2) * v2;
		}
	}
	else
	{
		if(d2>0)
		{
			v2 = -d2 / (d1 - d2) * v1 + d1 / (d1 - d2) * v2;
		}
		else
		{
			//Nothing
		}
	}

	// v0,v1,v2 represents a fully submerged triangle
	float32 k_inv3 = 1.0f / 3.0f;

	// Area weighted centroid
	*c = k_inv3 * (v0 + v1 + v2);

	b2Vec2 e1 = v1 - v0;
	b2Vec2 e2 = v2 - v0;

	return 0.5f * b2Cross(e1, e2);
}