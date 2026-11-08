// import "./index.css";
// import { Composition } from "remotion";
// import { HelloWorld, myCompSchema } from "./HelloWorld";
// import { Logo, myCompSchema2 } from "./HelloWorld/Logo";

import "./index.css";
import { Composition } from "remotion";
import { KaraokeVideo } from "./KaraokeVideo";
// import { Travel } from "./compositions/Travel";

export const RemotionRoot = () => {
  return (
    <Composition
      id="Karaoke"
      component={KaraokeVideo}
      durationInFrames={24 * 20} // adjust later
      fps={24}
      width={640}
      height={640}
    />
    // <Composition
    //   id="Travel"
    //   component={Travel}
    //   durationInFrames={600}
    //   fps={24}
    //   height={720}
    //   width={1280}
    // />
  );
};