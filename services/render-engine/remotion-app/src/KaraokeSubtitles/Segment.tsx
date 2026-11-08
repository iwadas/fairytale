import { interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { Word } from "./Word";

export const Segment: React.FC<{
  segment: any;
}> = ({ segment }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const time = frame / fps;

  if (time < segment.start || time > segment.end + 0.2) {
    return null;
  }

  const opacity = interpolate( time, [segment.end - 0.1, segment.end + 0.2], [1, 0], { easing: Easing.out(Easing.cubic), } );

  return (
    <div className="absolute bottom-40 w-full flex justify-center px-10">
      <div className="text-lg leading-tight text-center flex flex-wrap justify-center" style={{ width: `50%`, opacity }}>
        {segment.words.map((w: any, i: number) => (
          <Word key={i} {...w} />
        ))}
      </div>
    </div>
  );
};