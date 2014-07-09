uniform vec3 color;

#define zOffset 0.1

void main()
{
	gl_FragColor.rgb = color;
	gl_FragDepth = gl_FragCoord.z * zOffset;

}
