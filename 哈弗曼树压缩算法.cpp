#include<bits/stdc++.h>
using namespace std;

#define BUFFER_SIZE 1024
#define CHAR_COUNT_LEN 256

// 哈夫曼树的结点结构 
struct huffman_node {
	size_t times; // 本字符出现的次数 
	unsigned char val; // 字符的值 
	huffman_node *left; // 左孩子 
	huffman_node *right; // 右孩子 
};

size_t char_count_info[CHAR_COUNT_LEN] = {}; // 统计出现字符频率
vector<huffman_node *> huffman_tree_nodes; // 动态数组用于存储哈夫曼树的结点
huffman_node *huffman_tree_root = NULL; // 哈夫曼树的根结点 
map<unsigned char, string> huffman_codes_table; // 用于存储哈夫曼编码

// 打印哈夫曼编码表
void print_huffman_codes_table(map<unsigned char, string> huffman_codes_table) {
    printf("the huffman codes is:\n");
    for(map<unsigned char, string>::iterator it = huffman_codes_table.begin(); 
		it != huffman_codes_table.end(); it++) {
        printf("character '%c'(%d) : %s\n", 
               (it->first >= 32 && it->first <= 126) ? it->first : '?', 
               it->first, it->second.c_str());
    }
    printf("\n");
}

// 生成哈夫曼编码表（递归函数）
void generate_huffman_codes_table(huffman_node* root, string code) {
    if(root == NULL) return;
    
    // 如果是叶子节点，保存编码
    if(root->left == NULL && root->right == NULL) {
        huffman_codes_table[root->val] = code;
    } else {
    	// 递归处理左右子树
	    generate_huffman_codes_table(root->left, code + "0");
	    generate_huffman_codes_table(root->right, code + "1");
	}
}

// 排序辅助函数 
bool cmp(huffman_node *a,huffman_node *b){
	return a->times > b->times;
}

// 创建哈弗曼树 
int generate_huffman_tree() {
	printf("begin generate huffman tree......\n");
	while(huffman_tree_nodes.size() > 1) {
		// 按照字符出现频率进行降序排序 
		sort(huffman_tree_nodes.begin(), huffman_tree_nodes.end(), cmp);
		
		// 取出字符出现频率最小的两个 
		huffman_node *min1 = huffman_tree_nodes.back();
		huffman_tree_nodes.pop_back();
		huffman_node *min2 = huffman_tree_nodes.back();
		huffman_tree_nodes.pop_back();
		
		// 生成新的父亲结点，频率最小的结点作为左孩子 
		huffman_node *cur = (huffman_node *) malloc(sizeof(huffman_node));
		cur->times = min1->times + min2->times;
		cur->left = min1;
		cur->right = min2;
		
		huffman_tree_nodes.push_back(cur); 
		huffman_tree_root = cur; 
	}
	printf("success generate huffman tree\n\n");
	return 0;
}



// 逐一生成哈夫曼树结点，并存储于全局变量 tree_nodes 中 
int generate_huffman_tree_nodes()
{
	printf("begin generate huffman tree nodes......\n");
	
	int nodes_count = 0; // 统计生成了多少个结点 
	for(int i = 0; i < CHAR_COUNT_LEN; i++) {
		// 出现次数为 0 的字符不需要生成结点 
		if(char_count_info[i] > 0) {
			nodes_count++;
			huffman_node *cur = (huffman_node *) malloc(sizeof(huffman_node));
			cur->val = i;
			cur->times = char_count_info[i];
			cur->left = NULL;
			cur->right = NULL;
			
			huffman_tree_nodes.push_back(cur);
		} 
	}
	printf("success generate %d huffman tree nodes\n\n", nodes_count);
	return 0; 
} 

// 用于统计每个字符在文件出现的次数
// 统计结果存储在全局变量 char_count_info 中 
int count_char(unsigned char buffer[], size_t len)
{
	for(size_t i = 0; i < len; i++) {
		char_count_info[buffer[i]]++;
	}
	return 0;
}

// 读取指定文件内容，并统计字符出现的次数 
int count_file_char(char *file_name)
{
	FILE *file; // 打开文件句柄  
    
    file = fopen(file_name, "rb");
    if (file == NULL) {
        printf("can't open file [%s], please check file name!\n", file_name);
        return -1;
    }
    
    unsigned char buffer[BUFFER_SIZE] = {}; // 读取文件时的缓冲区 
    size_t bytes_read = 0; // 每次读了多少个字节 
    size_t read_times_count = 1; // 总共读取了多少次了
    
    // 循环读取直到文件结束，1 表示每次读取的数据块大小，单位为字节 
    while ((bytes_read = fread(buffer, 1, BUFFER_SIZE, file)) > 0) {
        printf("the %zu th read, read %zu byte! process......\n", 
				read_times_count, bytes_read);
        count_char(buffer, bytes_read);
        read_times_count++;
    }
    
    fclose(file);
    printf("success read file: [%s] and count char\n\n", file_name);
    return 0;
}

int compress_file(char *input_file_name, char *output_file_name) {
	printf("begin cmpress [%s] -> [%s]\n", input_file_name, output_file_name);
    
    FILE *input = fopen(input_file_name, "rb");
    FILE *output = fopen(output_file_name, "wb");
    
    if(input == NULL || output == NULL) {
    	printf("can't open file [%s] or [%s], please check file name!\n", 
				input_file_name, output_file_name);
        return -1;
    }
    
    // 3. 压缩数据
    unsigned char buffer[BUFFER_SIZE]; // 文件读取缓冲器 
    size_t bytes_read; // 已经读取了多少字节 
    unsigned char current_byte = 0; // 当前字节 
    int bit_count = 0; // 已经处理了多少个二进制位 
    
    while((bytes_read = fread(buffer, 1, BUFFER_SIZE, input)) > 0) {
    	for(size_t i = 0; i < bytes_read; i++) {
            string code = huffman_codes_table[buffer[i]];
            int code_length = code.length();
            
            for(int j = 0; j < code_length; j++) {
            	char bit = code[j];
            	current_byte <<= 1; // 左移 1 位
				if(bit == '1') {
					current_byte |= 1;
				} 
            	
            	bit_count++;
				
				if(bit_count == 8) { // 凑齐了 8 位（1 个字节） 
					fputc(current_byte, output);
					current_byte = 0; // 清零，继续下一个字节 
					bit_count  = 0;
				}
			}
		}
	}
	
	// 处理最后一个不完整的字节
	if(bit_count > 0) {
		current_byte <<= (8 - bit_count); // 左移补齐 0
		fputc(current_byte, output);
        // 记录最后一个字节的有效位数
        fputc(bit_count, output);
	} else {
		fputc(8, output); // 表示最后一个字节是完整的
	}
	
	fclose(input);
    fclose(output);
    printf("success compress file: [%s] to [%s]\n\n", input_file_name, output_file_name);
    return 0;
}

// 获取指定文件大小 
size_t get_file_size(char *file_name) {
	FILE *fp = fopen(file_name, "rb");
	if (fp == NULL) {
		printf("can't open file [%s], please check file name!\n", file_name);
		return -1;
	}
	fseek(fp, 0, SEEK_END);
	size_t file_size = ftell(fp);
	fclose(fp);
	return file_size;
}

int uncompress_file(char *input_file_name, char *output_file_name) {
	printf("begin uncmpress [%s] -> [%s]\n", input_file_name, output_file_name);
    size_t input_file_size = get_file_size(input_file_name);
    
    FILE *input = fopen(input_file_name, "rb");
    FILE *output = fopen(output_file_name, "wb");
    
    if(input == NULL || output == NULL) {
    	printf("can't open file [%s] or [%s], please check file name!\n", 
				input_file_name, output_file_name);
        return -1;
    }
    
    huffman_node *current_node = huffman_tree_root; // 用于记录当前在哪个结点 
    unsigned char cur_byte; // 当前读取的字节 
    int byte_bits = 8; // 默认最后一个字节完整
    long bytes_decoded = 0; // 已经解码的字节
    
	while(bytes_decoded < input_file_size) {
		cur_byte = fgetc(input);
		bytes_decoded++;
		
		// 需要对最后一个字节处理，因为最后一个字节可能不满
		if(bytes_decoded == input_file_size-1) {
			int bit_count = fgetc(input); // 最后一个字节有效位数 
			byte_bits = 8 - bit_count;
		} 
		
		for(int i = 7; i >= 8 - byte_bits; i--) {
			int bit = (cur_byte >> i) & 1;
			if(bit) { // 1 往右走 
				current_node = current_node->right;
			} else { // 0 往左走 
				current_node = current_node->left;
			}
			
			// 如果到达叶子节点
            if(!current_node->left && !current_node->right) {
            	// 将当前结点的 val 写入文件 
                fputc(current_node->val, output);  
                current_node = huffman_tree_root; // 回到根节点 
            }
		}
	}
	printf("success uncompress file: [%s] to [%s]\n\n", input_file_name, output_file_name);
    return 0;
}

// 释放哈夫曼树 
void destroy_huffman_tree(huffman_node* root) {
    if (root == NULL) return;
    destroy_huffman_tree(root->left);
    destroy_huffman_tree(root->right);
    free(root);
}

// 哈夫曼函数 
int huffman(char *file_name)
{
	// 压缩后的文件名 
	char compress_file_name[strlen(file_name) + 8];
	// 解压缩后的文件名 
	char uncompress_file_name[strlen(file_name) + 11];
	strcpy(compress_file_name, file_name);
	strcat(compress_file_name, ".huffman");
	
	strcpy(uncompress_file_name, "uncompress_");
	strcat(uncompress_file_name, file_name);

	count_file_char(file_name);
	generate_huffman_tree_nodes();
	generate_huffman_tree();
	
	huffman_node *root = huffman_tree_root; 
	generate_huffman_codes_table(root, "");
	print_huffman_codes_table(huffman_codes_table);
	compress_file(file_name, compress_file_name);
	uncompress_file(compress_file_name, uncompress_file_name);
	destroy_huffman_tree(huffman_tree_root);
}

int main(int argc, char** argv)
{
	if(argc < 2) {
		printf("usage: %s <filename>\n", argv[0]);
		return -1;
	} else {
		printf("the file is [%s]\n", argv[1]);
		return huffman(argv[1]);
	}
	return 0;
}
