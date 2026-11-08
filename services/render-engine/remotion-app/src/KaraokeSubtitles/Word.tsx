import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
} from "remotion";

export const Word: React.FC<{
  word: string;
  start: number;
  end: number;
  isSpecial?: boolean;
}> = ({ word, start, end, isSpecial }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // const time = frame / fps;

  // const isVisible = time >= start;
  // const isActive = time >= start && time <= end;

  // smooth entrance (spring > looks much better than linear)
  // const enterProgress = spring({
  //   frame: Math.max(0, frame - start * fps),
  //   fps,
  //   config: {
  //     damping: 12,
  //     stiffness: 120,
  //   },
  // });

  const translateY = interpolate(
    frame, [start * fps, end * fps], [12, 0],
    {
      easing: Easing.out(Easing.cubic),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  const opacity = interpolate(
    frame, [start * fps, end * fps], [0, 1],
    {
      easing: Easing.out(Easing.cubic),
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );



  // subtle pop when active
  // const scale = isActive
  //   ? interpolate(time, [start, end], [1, 1.1], {
  //       extrapolateRight: "clamp",
  //     })
  //   : 1;

  // if (!isVisible) return null;

  return (
    <span
      className={`
        inline-block mr-3
        font-bold tracking-tight
        ${isSpecial ? "text-yellow-400" : "text-white"}
      `}
      style={{
        transform: `translateY(${translateY}px)`,
        opacity,
        textShadow: `
          0 0 10px rgba(0, 0, 0, 0.7),
          0 0 20px rgba(0, 0, 0, 0.5)
        `
      }}
    >
      {word} {isSpecial}
    </span>
  );
};