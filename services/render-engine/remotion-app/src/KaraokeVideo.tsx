import { AbsoluteFill } from "remotion";
import { segments } from "./data/example.data";
import { Segment } from "./KaraokeSubtitles/Segment";

export const KaraokeVideo: React.FC = () => {
  return (
    <AbsoluteFill className="flex items-center justify-center">
      {segments.map((segment, i) => (
        <Segment key={i} segment={segment} />
      ))}
    </AbsoluteFill>
  );
};