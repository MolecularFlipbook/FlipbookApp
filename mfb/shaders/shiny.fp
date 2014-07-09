uniform vec3 color;
uniform vec3 highlight;
//uniform float select;
uniform float time;
uniform float gray;

varying vec3 p;
varying vec3 n;
varying vec3 hv;

#define ambient 0.4
#define zOffset 1.0
#define SELECTRGB vec3(0.0,1.0,0.0)

//=============

vec3 mod289(vec3 x) {return x - floor(x * (1.0 / 289.0)) * 289.0;}
vec2 mod289(vec2 x) {return x - floor(x * (1.0 / 289.0)) * 289.0;}
vec3 permute(vec3 x) {return mod289(((x*34.0)+1.0)*x);}

float snoise(vec2 v)
{
	const vec4 C = vec4(0.2113248654051, 0.3660254037844, -0.5773502691896, 0.0243902439024);
	// First corner
	vec2 i  = floor(v + dot(v, C.yy) );
	vec2 x0 = v -   i + dot(i, C.xx);

	// Other corners
	vec2 i1;
	//i1.x = step( x0.y, x0.x ); // x0.x > x0.y ? 1.0 : 0.0
	//i1.y = 1.0 - i1.x;
	i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
	// x0 = x0 - 0.0 + 0.0 * C.xx ;
	// x1 = x0 - i1 + 1.0 * C.xx ;
	// x2 = x0 - 1.0 + 2.0 * C.xx ;
	vec4 x12 = x0.xyxy + C.xxzz;
	x12.xy -= i1;

	// Permutations
	i = mod289(i); // Avoid truncation effects in permutation
	vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 )) + i.x + vec3(0.0, i1.x, 1.0 ));

	vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
	m = m*m ;
	m = m*m ;

	// Gradients: 41 points uniformly over a line, mapped onto a diamond.
	// The ring size 17*17 = 289 is close to a multiple of 41 (41*7 = 287)

	vec3 x = 2.0 * fract(p * C.www) - 1.0;
	vec3 h = abs(x) - 0.5;
	vec3 ox = floor(x + 0.5);
	vec3 a0 = x - ox;

	// Normalise gradients implicitly by scaling m
	// Approximation of: m *= inversesqrt( a0*a0 + h*h );
	m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );

	// Compute final noise value at P
	vec3 g;
	g.x  = a0.x  * x0.x  + h.x  * x0.y;
	g.yz = a0.yz * x12.xz + h.yz * x12.yw;
	return 130.0 * dot(m, g);
}

//=============

void main()
{

	// vary normal
	vec3 normal = normalize(n);

	// calculate lighting
	vec3 L = normalize(gl_LightSource[1].position.xyz - p);
	float diff = max(dot(normal + snoise(gl_TexCoord[0].xy*10.0)*0.02,L), 0.0);

	vec3 halfVec = normalize(hv);
	float nDotHV = max(dot(normal, halfVec), 0.0);
	float spec = pow(nDotHV, 100.0);

	// calculate rim
	float rim = 1.0-normal.z;

	// calculate surface color
	vec3 color = color*diff + color*ambient + spec + pow(rim, 3.0);

	// calculate gleam
	float gleam = sin((gl_FragCoord.x + gl_FragCoord.y+time*300.0)*0.02);
	gleam = (gleam * 0.5) + 0.7;

	// add hover highlight
	color +=  highlight * gleam;

	// add selection highlight
	/*if (select > 0.5 && false)
	{
		rim = pow(rim, 6.0);
		rim *= 10.0;
		if (rim<0.9)
		{
			rim = 0.0;
		}
		else
		{
			rim = 1.0;
		}

		color = mix(color, SELECTRGB,  rim);
	}*/

	if (gray > 0.5)
	{
		vec3 factor = vec3(0.3, 0.5, 0.2);
		float luma = dot(color, factor);
		color = mix(color, vec3(luma, luma, luma), 0.8);
		color = mix(color, vec3(1.0, 1.0, 1.0), 0.2);
	}

	vec4 finalColor = vec4(color.rgb, 1.0);
	gl_FragColor.rgba = finalColor;
	//gl_FragDepth = gl_FragCoord.z * 0.1;

}
