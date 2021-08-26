import torch
import torch.nn as nn
import math

device = torch.devices("cuda" if torch.cuda.is_available() else "cpu")

class PositionalEncoding(nn.Module):

    def __init__(self,emb_size,dropout,maxlen=5000):
        super(PositionalEncoding,self).__init__()
        #torch.arange returns 1D tensor
        den  = torch.exp(-torch.arange(0,emb_size,2)*math.log(1000)/emb_size)
        pos = torch.arange(0,maxlen).reshape(maxlen,1)
        pos_embedding = torch.zeros(maxlen,emb_size)
        pos_embedding[:,0::2] = torch.sin(pos*den)
        pos_embedding[:,1::2] = torch.cos(pos*den)
        
        print("Shape of pos embedding = ",pos_embedding.shape,end=" ")
        pos_embedding = pos_embedding.unsqueeze(-2)
        print("Shape of pos embedding = ",pos_embedding.shape,end=" ")

        self.dropout = nn.Dropout(dropout)
        self.register_buffer('pos_embedding',pos_embedding)

    def forward(self,token_embedding):
        return self.dropout(token_embedding+self.pos_embedding[:token_embedding.size(0),:])


class TokenEmbedding(nn.Module):
    def __init__(self,vocab_size,emb_size):
        super(TokenEmbedding,self).__init__()
        self.embedding = nn.Embedding(vocab_size,emb_size)
        self.emb_size = emb_size

    def forward(self,tokens):
        return self.embedding(tokens.long()) * math.sqrt(self.emb_size)

class S2S_Transformer(nn.Module):

    def __init__(
        self,
        num_encoder_layers,
        num_decoder_layers,
        emb_size,
        nhead,
        src_vocab_size,
        tgt_vocab_size,
        dim_feedforward=512,
        dropout=0.1
    ) -> None:
        
        super(S2S_Transformer,self).__init__()

        self.transformer = nn.Transformer(
            d_model=emb_size,
            nhead=nhead,
            num_encoder_layers=num_encoder_layers,
            num_decoder_layers=num_decoder_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
        )
        
        self.generator = nn.Linear(emb_size, tgt_vocab_size)
        self.src_tok_emb = TokenEmbedding(src_vocab_size,emb_size)
        self.tgt_tok_emb = TokenEmbedding(tgt_vocab_size,emb_size)
        self.positional_encoding = PositionalEncoding(emb_size,dropout=dropout)

    def forward(
        self,
        src:Tensor,
        tgt:Tensor,
        src_mask:Tensor,
        tgt_mask:Tensor,
        src_padding_mask:Tensor,
        tgt_padding_mask:Tensor,
        memory_key_padding_mask:Tensor
        ):

        src_emb = self.positional_encoding(self.src_tok_emb(src))
        tgt_emb = self.positional_encoding(self.tgt_tok_emb(tgt))

        out = self.transformer(
            src_emb,
            tgt_emb,
            src_mask,
            tgt_mask,
            None,
            src_padding_mask,
            tgt_padding_mask,
            memory_key_padding_mask
        )

        return self.generator(out)

    def encode(self,src,src_mask):
   
        return self.transformer.encoder(
            self.positional_encoding(self.src_tok_emb(src)),
            src_mask
        )
    
    def decode(self,tgt,memory,tgt_mask):
        
        return self.transformer.decoder(
            self.positional_encoding(self.tgt_tok_emb(tgt)),
            memory,
            tgt_mask
        )



    