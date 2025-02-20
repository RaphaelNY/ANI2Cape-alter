from PIL import Image
import io,os,sys
import logging

logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',level=logging.INFO)

def analyzeANIFile(filePath):
    with open(filePath,'rb') as f:
        if f.read(4) != b'RIFF':
            return {"code":-1,"msg":"File is not a ANI File!"}
        logging.debug('文件头检查完成！')
        fileSize = int.from_bytes(f.read(4), byteorder='little', signed=False)
        # if os.path.getsize(filePath) != fileSize:
        #     return {"code":-2,"msg":"File is damaged!"}
        logging.debug('文件长度检查完成！')
        if f.read(4) != b'ACON':
            return {"code":-1,"msg":"File is not a ANI File!"}
        logging.debug('魔数检查完成！')
        frameRate = (1/60)*1000
        while(True):
            chunkName = f.read(4)
            if chunkName == b'LIST':
                break
            chunkSize = int.from_bytes(f.read(4), byteorder='little', signed=False)
            if chunkName.lower() == b'rate':
                logging.debug('发现自定义速率！')
                frameRate = frameRate * int.from_bytes(f.read(4), byteorder='little', signed=False)
                logging.warning('发现自定义速率！由于GIF限制，将取第一帧与第二帧的速率作为整体速率！')
                f.read(chunkSize - 4)
            else:
                logging.debug('发现自定义Chunk！')
                f.read(chunkSize)
        listChunkSize = int.from_bytes(f.read(4), byteorder='little', signed=False)
        if f.read(4) != b'fram':
            return {"code":-3,"msg":"File not a ANI File!(No Frames)"}
        logging.debug('frame头检查完成！')
        frameList = []
        nowSize = 4
        while(nowSize < listChunkSize):
            if f.read(4) != b'icon':
                return {"code":-4,"msg":"File not a ANI File!(Other Kind Frames)"}
            nowSize += 4
            subChunkSize = int.from_bytes(f.read(4), byteorder='little', signed=False)
            nowSize += 4
            frameList.append(f.read(subChunkSize))
            nowSize += subChunkSize
        return {"code":0,"msg":frameList,"frameRate":frameRate}

if __name__ == '__main__':
    OUTPUT_SIZE = (48, 48)
    
    if len(sys.argv) < 2:
        logging.fatal("Usage: python ani2spritesheet.py <inputFileOrDir> <outputFileOrDir,Option>")
    else:
        inputPath = sys.argv[1]
        outputPath = sys.argv[2] if len(sys.argv) > 2 else inputPath 

        if os.path.isdir(inputPath):
            if not os.path.exists(outputPath):
                os.makedirs(outputPath) 
            for filename in os.listdir(inputPath):
                if filename.lower().endswith('.ani'):
                    filePath = os.path.join(inputPath, filename)
                    res = analyzeANIFile(filePath)
                    
                    if res["code"] == 0:
                        logging.info(f'ANI文件 {filename} 分析完成，帧提取完成！')
                        output = Image.new("RGBA", (OUTPUT_SIZE[0], OUTPUT_SIZE[1] * len(res["msg"])))
                        for frameIndex in range(len(res["msg"])):
                            frameImage = Image.open(io.BytesIO(res["msg"][frameIndex]), formats=['cur']).convert('RGBA')
                            extracted_frame = frameImage.resize(OUTPUT_SIZE)
                            position = (0, OUTPUT_SIZE[1] * frameIndex)
                            output.paste(extracted_frame, position)

                        outputFilePath = os.path.join(outputPath, f"{filename.strip('.ani')}.png")
                        output.save(outputFilePath, format="PNG")
                        logging.info(f'SpriteSheet {filename} 生成完成！')
                    else:
                        logging.fatal(res["msg"])
        
        elif os.path.isfile(inputPath):
            res = analyzeANIFile(inputPath)
            
            if res["code"] == 0:
                logging.info(f'ANI文件 {inputPath} 分析完成，帧提取完成！')
                output = Image.new("RGBA", (OUTPUT_SIZE[0], OUTPUT_SIZE[1] * len(res["msg"])))
                for frameIndex in range(len(res["msg"])):
                    frameImage = Image.open(io.BytesIO(res["msg"][frameIndex]), formats=['cur']).convert('RGBA')
                    extracted_frame = frameImage.resize(OUTPUT_SIZE)
                    position = (0, OUTPUT_SIZE[1] * frameIndex)
                    output.paste(extracted_frame, position)

                if os.path.isdir(outputPath):
                    outputFilePath = os.path.join(outputPath, f"{os.path.basename(inputPath).strip('.ani')}.png")
                else:
                    outputFilePath = outputPath
                output.save(outputFilePath, format="PNG")
                logging.info(f'SpriteSheet {os.path.basename(inputPath)} 生成完成！')
            else:
                logging.fatal(res["msg"])
        
        else:
            logging.fatal("Invalid input path!")
