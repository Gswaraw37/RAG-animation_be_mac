#!/usr/bin/env python3
"""
Manual PDF Processing Script - Method 1
Process PDF file step by step dengan full debugging
Updated: chunk_size=1000, chunk_overlap=300
"""

import sys
import os
import gc
import time
from datetime import datetime

# Set environment untuk fix model issues
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'

def manual_process_pdf(file_id=1):
    """Manual PDF processing dengan full debugging"""
    
    print(f"🚀 MANUAL PDF PROCESSING - File ID: {file_id}")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Import dependencies
        print("📦 Step 1: Importing dependencies...")
        sys.path.append('/app')
        
        from database import get_db_connection, update_file_processed_status
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
        from langchain_chroma import Chroma
        from config import Config
        
        print("   ✅ All dependencies imported successfully")
        
        # Get file info from database
        print("\n📋 Step 2: Getting file info from database...")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM uploaded_files WHERE id = %s", (file_id,))
        file_info = cursor.fetchone()
        
        if not file_info:
            print(f"   ❌ File with ID {file_id} not found in database")
            return False
            
        file_path = file_info['filepath']
        filename = file_info['filename']
        
        print(f"   ✅ File found: {filename}")
        print(f"   📍 Path: {file_path}")
        
        # Check if file exists
        print("\n📄 Step 3: Checking file existence...")
        if not os.path.exists(file_path):
            print(f"   ❌ File not found at: {file_path}")
            return False
            
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        print(f"   ✅ File exists")
        print(f"   📊 Size: {file_size:.2f} MB")
        
        # Load PDF
        print("\n📖 Step 4: Loading PDF...")
        start_time = time.time()
        
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        load_time = time.time() - start_time
        print(f"   ✅ PDF loaded successfully")
        print(f"   📄 Pages: {len(documents)}")
        print(f"   ⏱️  Load time: {load_time:.2f} seconds")
        
        # Show sample content
        if documents and len(documents[0].page_content) > 0:
            sample = documents[0].page_content[:150].replace('\n', ' ')
            print(f"   📝 Sample text: {sample}...")
        
        # Text splitting - UPDATED SETTINGS
        print("\n✂️  Step 5: Splitting text into chunks...")
        print(f"   ⚙️  Settings: chunk_size=1000, chunk_overlap=300")
        start_time = time.time()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,     # Updated chunk size
            chunk_overlap=300,   # Updated overlap
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        split_time = time.time() - start_time
        
        print(f"   ✅ Text splitting completed")
        print(f"   📦 Total chunks: {len(chunks)}")
        print(f"   ⏱️  Split time: {split_time:.2f} seconds")
        
        # Show sample chunk
        if chunks:
            sample_chunk = chunks[0].page_content[:100].replace('\n', ' ')
            print(f"   📝 Sample chunk: {sample_chunk}...")
        
        # Free memory dari documents
        del documents
        gc.collect()
        print("   🗑️  Freed documents memory")
        
        # Initialize embedding model
        print("\n🤖 Step 6: Loading embedding model...")
        start_time = time.time()
        
        model_name = Config.EMBEDDING_MODEL_NAME or 'intfloat/multilingual-e5-small'
        print(f"   📦 Model: {model_name}")
        
        embedding_function = SentenceTransformerEmbeddings(model_name=model_name)
        
        model_time = time.time() - start_time
        print(f"   ✅ Embedding model loaded")
        print(f"   ⏱️  Model load time: {model_time:.2f} seconds")
        
        # Test single embedding
        print("\n🧪 Step 7: Testing embedding generation...")
        start_time = time.time()
        
        if chunks:
            test_text = chunks[0].page_content[:500]  # Increased test text limit for larger chunks
            test_embedding = embedding_function.embed_query(test_text)
            
            test_time = time.time() - start_time
            print(f"   ✅ Embedding test successful")
            print(f"   📐 Embedding dimensions: {len(test_embedding)}")
            print(f"   ⏱️  Test time: {test_time:.2f} seconds")
        
        # Initialize ChromaDB
        print("\n🗄️  Step 8: Connecting to ChromaDB...")
        start_time = time.time()
        
        print(f"   📂 Chroma directory: {Config.CHROMA_PERSIST_DIRECTORY}")
        print(f"   🏷️  Collection name: {Config.COLLECTION_NAME}")
        
        vectorstore = Chroma(
            persist_directory=Config.CHROMA_PERSIST_DIRECTORY,
            embedding_function=embedding_function,
            collection_name=Config.COLLECTION_NAME
        )
        
        db_time = time.time() - start_time
        print(f"   ✅ ChromaDB connected")
        print(f"   ⏱️  Connection time: {db_time:.2f} seconds")
        
        # Process embeddings in batches
        print(f"\n🔄 Step 9: Processing {len(chunks)} chunks...")
        print(f"   📦 Batch processing for memory efficiency")
        
        batch_size = 5  # Slightly larger batches since chunks are bigger but more efficient
        success_count = 0
        failed_count = 0
        total_batches = ((len(chunks) - 1) // batch_size) + 1
        
        print(f"   📊 Total batches: {total_batches} (size: {batch_size})")
        print()
        
        overall_start = time.time()
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"   📦 Batch {batch_num}/{total_batches}: Processing {len(batch_chunks)} chunks...")
            
            try:
                batch_start = time.time()
                
                # Add to vectorstore
                vectorstore.add_documents(batch_chunks)
                
                batch_time = time.time() - batch_start
                success_count += len(batch_chunks)
                
                print(f"      ✅ Batch {batch_num} completed in {batch_time:.2f}s")
                
                # Memory cleanup after each batch
                gc.collect()
                
                # Small delay to prevent overload
                time.sleep(0.5)
                
            except Exception as batch_error:
                failed_count += len(batch_chunks)
                print(f"      ❌ Batch {batch_num} failed: {str(batch_error)[:100]}")
                continue
        
        overall_time = time.time() - overall_start
        
        print(f"\n   📊 Batch Processing Summary:")
        print(f"      ✅ Successful: {success_count} chunks")
        print(f"      ❌ Failed: {failed_count} chunks")
        print(f"      ⏱️  Total time: {overall_time:.2f} seconds")
        print(f"      📈 Success rate: {(success_count/(success_count+failed_count)*100):.1f}%")
        
        # Update database if successful
        if success_count > 0:
            print(f"\n💾 Step 10: Updating database...")
            update_file_processed_status(file_id)
            print(f"   ✅ Database updated - file marked as processed")
        else:
            print(f"\n💥 Step 10: Database NOT updated (no successful chunks)")
        
        # Cleanup
        cursor.close()
        conn.close()
        
        # Final summary
        total_time = time.time()
        print(f"\n🎉 MANUAL PROCESSING COMPLETED!")
        print("=" * 60)
        print(f"📋 FINAL SUMMARY:")
        print(f"   📄 File: {filename}")
        print(f"   📊 Size: {file_size:.2f} MB")
        print(f"   📄 Pages: {len(documents) if 'documents' in locals() else 'N/A'}")
        print(f"   📦 Chunks created: {len(chunks)}")
        print(f"   ✅ Chunks processed: {success_count}")
        print(f"   📈 Success rate: {(success_count/len(chunks)*100):.1f}%")
        print(f"   ⚙️  Chunk settings: size=1000, overlap=300")
        print(f"   🏁 Final status: {'SUCCESS' if success_count > 0 else 'FAILED'}")
        print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during manual processing:")
        print(f"❌ Error: {e}")
        print("\n🔍 Full traceback:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 MANUAL PDF PROCESSING TOOL (Updated Settings)")
    print("=" * 60)
    print("⚙️  Configuration: chunk_size=1000, chunk_overlap=300")
    print()
    
    # Get file ID dari command line atau default ke 1
    if len(sys.argv) > 1:
        try:
            file_id = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid file ID. Using default ID: 1")
            file_id = 1
    else:
        file_id = 1
        
    print(f"🎯 Target file ID: {file_id}")
    print()
    
    # Run manual processing
    success = manual_process_pdf(file_id)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESS: Manual processing completed!")
        print("✅ File is now in vector database and ready for RAG queries")
    else:
        print("💥 FAILED: Manual processing was unsuccessful")
        print("🔧 Check error messages above for debugging info")
        print("⏭️  Consider skipping this file if it consistently fails")
        
    print("\n📋 NEXT STEPS:")
    if success:
        print("   🔍 Test RAG queries with the processed file")
        print("   ➡️  Continue with normal application operation")
    else:
        print("   🔧 Debug the specific error messages above")
        print("   📄 Check if PDF file is corrupted or encrypted")
        print("   ⏭️  Skip this file and try processing other files")
        print("   💾 Consider increasing memory limits if OOM errors")
